// ============================================================
// FlotaTrack - ESP32 (C++ / Arduino framework)
// Telemetria GPS + nivel de combustible + kill switch (LED)
// Libreria necesaria: ArduinoJson v7 (Gestor de librerias)
// ============================================================

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ============================================================
// CONFIGURACION - AJUSTA ESTOS VALORES
// ============================================================

const char* WIFI_SSID     = "WIFINOMBRE";
const char* WIFI_PASSWORD = "CONTRASENA";

const char* API_URL_BASE = "URLUSADO";  // IP/dominio real del backend (con http://)
const char* TRUCK_ID     = "ID DEL CAMION QUE SE VA A USAR";

const unsigned long INTERVALO_ENVIO = 15;  // segundos entre cada envio

// Calibracion del sensor ultrasonico (distancia sensor -> superficie, en cm)
const float DISTANCIA_TANQUE_VACIO = 40.0;  // cm con el tanque vacio
const float DISTANCIA_TANQUE_LLENO = 5.0;   // cm con el tanque lleno

// Pines
const int PIN_GPS_RX = 16;  // RX del ESP32 <- TX del GPS
const int PIN_GPS_TX = 17;  // TX del ESP32 -> RX del GPS
const int PIN_TRIG   = 5;
const int PIN_ECHO   = 18;
const int PIN_LED    = 4;   // encendido = motor deshabilitado (kill switch activo)

// ============================================================
// ESTADO GLOBAL
// ============================================================

HardwareSerial gps(2);  // UART2 dedicada al GPS

String buffer_gps = "";
bool   tiene_fix = false;     // equivale a ultima_lat/lon distintas de None
double ultima_lat = 0.0;
double ultima_lon = 0.0;
float  ultima_velocidad = 0.0;

String ultimo_command_id_pendiente = "";

bool wifi_ok = false;
unsigned long ultimo_envio = 0;
float ultimo_combustible_valido = 0.0;  // respaldo si el sensor falla

// ============================================================
// UTILIDADES
// ============================================================

// Separa una cadena por comas CONSERVANDO los campos vacios
// (igual que str.split(",") en Python). Devuelve cuantos campos hubo.
int dividir_por_comas(const String& texto, String* partes, int max_partes) {
  int n = 0;
  int inicio = 0;
  while (n < max_partes) {
    int pos = texto.indexOf(',', inicio);
    if (pos < 0) {
      partes[n++] = texto.substring(inicio);
      break;
    }
    partes[n++] = texto.substring(inicio, pos);
    inicio = pos + 1;
  }
  return n;
}

// ============================================================
// WIFI
// ============================================================

bool conectar_wifi() {
  // Reinicia el adaptador para evitar "Wifi Internal State Error"
  WiFi.mode(WIFI_OFF);
  delay(1000);
  WiFi.mode(WIFI_STA);
  delay(1000);

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Conectando a WiFi...");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    // Hasta 20 s (40 intentos x 0.5 s)
    int intentos = 0;
    while (WiFi.status() != WL_CONNECTED && intentos < 40) {
      delay(500);
      intentos++;
    }
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi conectado: ");
    Serial.println(WiFi.localIP());
    return true;
  }

  Serial.println("No se pudo conectar a WiFi (revisa que la red sea de 2.4GHz)");
  return false;
}

// ============================================================
// SENSOR ULTRASONICO (NIVEL DE COMBUSTIBLE)
// ============================================================

// Devuelve la distancia en cm, o -1 si hubo timeout.
float medir_distancia_cm() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  // Duracion del pulso en alto del ECHO, timeout de 30 ms (0 = sin respuesta)
  unsigned long duracion = pulseIn(PIN_ECHO, HIGH, 30000);
  if (duracion == 0) {
    return -1.0;
  }

  // 0.0343 cm/us = velocidad del sonido; /2 por ida y vuelta
  return (duracion * 0.0343f) / 2.0f;
}

// Devuelve el porcentaje (0-100, 1 decimal) o -1 si la distancia es invalida.
float calcular_porcentaje_combustible(float distancia_cm) {
  if (distancia_cm < 0) {
    return -1.0;
  }

  float rango = DISTANCIA_TANQUE_VACIO - DISTANCIA_TANQUE_LLENO;
  float porcentaje = (DISTANCIA_TANQUE_VACIO - distancia_cm) / rango * 100.0f;

  porcentaje = max(0.0f, min(100.0f, porcentaje));
  return roundf(porcentaje * 10.0f) / 10.0f;
}

// ============================================================
// LED INDICADOR (KILL SWITCH)
// LED encendido = motor deshabilitado
// ============================================================

void activar_motor() {
  digitalWrite(PIN_LED, LOW);
  Serial.println("Kill switch: motor habilitado");
}

void desactivar_motor() {
  digitalWrite(PIN_LED, HIGH);
  Serial.println("Kill switch: motor deshabilitado");
}

// ============================================================
// GPS
// ============================================================

// Convierte coordenada NMEA ("ddmm.mmmm" / "dddmm.mmmm") a grados decimales.
bool convertir_a_decimal(const String& valor_crudo, const String& direccion, double& resultado) {
  if (valor_crudo.length() == 0) {
    return false;
  }

  double grados, minutos;
  if (direccion == "E" || direccion == "W") {
    if (valor_crudo.length() < 4) return false;
    grados  = valor_crudo.substring(0, 3).toInt();
    minutos = valor_crudo.substring(3).toDouble();
  } else {
    if (valor_crudo.length() < 3) return false;
    grados  = valor_crudo.substring(0, 2).toInt();
    minutos = valor_crudo.substring(2).toDouble();
  }

  double decimal = grados + (minutos / 60.0);

  if (direccion == "S" || direccion == "W") {
    decimal = -decimal;
  }

  resultado = decimal;
  return true;
}

// Parsea $GPGGA / $GNGGA. Devuelve true si hay fix valido.
bool parsear_gpgga(const String& trama, double& lat, double& lon) {
  String partes[15];
  int n = dividir_por_comas(trama, partes, 15);

  if (n < 10) {
    return false;  // trama incompleta
  }

  // Campo 6: calidad del fix ('0' = sin fix)
  if (partes[6] == "0" || partes[6] == "") {
    return false;
  }

  double la, lo;
  if (!convertir_a_decimal(partes[2], partes[3], la)) return false;
  if (!convertir_a_decimal(partes[4], partes[5], lo)) return false;

  lat = la;
  lon = lo;
  return true;
}

// Parsea $GPVTG / $GNVTG. Velocidad en km/h = campo 7.
bool parsear_gpvtg(const String& trama, float& velocidad) {
  String partes[10];
  int n = dividir_por_comas(trama, partes, 10);

  if (n < 8) {
    return false;
  }

  String cruda = partes[7];
  if (cruda.length() == 0) {
    return false;
  }

  velocidad = cruda.toFloat();
  return true;
}

void procesar_linea_gps(const String& linea) {
  if (linea.startsWith("$GPGGA") || linea.startsWith("$GNGGA")) {
    double lat, lon;
    if (parsear_gpgga(linea, lat, lon)) {
      ultima_lat = lat;
      ultima_lon = lon;
      tiene_fix = true;
    }
  } else if (linea.startsWith("$GPVTG") || linea.startsWith("$GNVTG")) {
    float velocidad;
    if (parsear_gpvtg(linea, velocidad)) {
      // Por debajo de 5 km/h se considera ruido del GPS
      ultima_velocidad = (velocidad >= 5.0f) ? velocidad : 0.0f;
    }
  }
}

// Lee los bytes disponibles y procesa cada linea completa.
void actualizar_gps() {
  while (gps.available()) {
    char c = (char)gps.read();
    if ((uint8_t)c > 127) continue;  // ignora bytes no ASCII
    buffer_gps += c;

    if (c == '\n') {
      buffer_gps.trim();
      if (buffer_gps.length() > 0) {
        procesar_linea_gps(buffer_gps);
      }
      buffer_gps = "";
    }
  }

  // Proteccion: si el buffer crece demasiado sin salto de linea, se descarta
  if (buffer_gps.length() > 512) {
    buffer_gps = "";
  }
}

// ============================================================
// ENVIO AL BACKEND
// ============================================================

void enviar_lectura(double lat, double lon, float velocidad, float combustible) {
  String url = String(API_URL_BASE) + "/devices/" + TRUCK_ID + "/telemetry";

  JsonDocument payload;
  payload["latitude"] = lat;
  payload["longitude"] = lon;
  payload["speed_kmh"] = velocidad;
  payload["fuel_level_pct"] = combustible;
  payload["acknowledged_command_id"] = ultimo_command_id_pendiente;

  String cuerpo;
  serializeJson(payload, cuerpo);

  HTTPClient http;
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  int status = http.POST(cuerpo);

  if (status <= 0) {
    // Error de red (WiFi caido, backend inalcanzable, etc.)
    Serial.print("Error enviando datos: ");
    Serial.println(HTTPClient::errorToString(status));
    http.end();
    return;
  }

  Serial.print("Enviado. Status: ");
  Serial.println(status);

  String respuesta = http.getString();

  if (status != 200 && status != 201) {
    Serial.print("Detalle del error: ");
    Serial.println(respuesta);
  }

  // Respuesta esperada:
  // {"received": true, "pending_command": {"type": "lock"|"unlock", "command_id": "..."}}
  JsonDocument data;
  DeserializationError err = deserializeJson(data, respuesta);

  if (!err) {
    JsonObject pendiente = data["pending_command"];

    if (!pendiente.isNull() && pendiente["type"].is<const char*>()) {
      String tipo = pendiente["type"].as<String>();

      if (tipo == "lock") {
        desactivar_motor();
      } else if (tipo == "unlock") {
        activar_motor();
      }

      // Se confirma hasta el SIGUIENTE envio
      ultimo_command_id_pendiente = pendiente["command_id"] | "";
    } else {
      ultimo_command_id_pendiente = "";
    }
  }
  // Si el JSON es invalido, simplemente no se procesa el comando pendiente

  http.end();
}

// ============================================================
// PROGRAMA PRINCIPAL
// ============================================================

void setup() {
  Serial.begin(115200);

  gps.begin(9600, SERIAL_8N1, PIN_GPS_RX, PIN_GPS_TX);

  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);  // motor habilitado al arrancar

  wifi_ok = conectar_wifi();
  if (!wifi_ok) {
    Serial.println("Sin WiFi, no se puede continuar");
  }

  ultimo_envio = millis();
}

void loop() {
  // Sin WiFi no tiene sentido seguir
  if (!wifi_ok) {
    delay(1000);
    return;
  }

  // Se vacia el buffer del GPS en cada vuelta para no perder tramas
  actualizar_gps();

  if (millis() - ultimo_envio > INTERVALO_ENVIO * 1000UL) {
    float distancia = medir_distancia_cm();
    float combustible = calcular_porcentaje_combustible(distancia);

    if (combustible < 0) {
      // Fallo el sensor: se reusa el ultimo valor valido (evita errores 422)
      Serial.println("Lectura de combustible fallo, se reusa el ultimo valor valido");
      combustible = ultimo_combustible_valido;
    } else {
      ultimo_combustible_valido = combustible;
    }

    Serial.print("Lat: ");
    if (tiene_fix) Serial.print(ultima_lat, 6); else Serial.print("None");
    Serial.print(" Lon: ");
    if (tiene_fix) Serial.print(ultima_lon, 6); else Serial.print("None");
    Serial.print(" Vel: ");
    Serial.print(ultima_velocidad);
    Serial.print(" km/h Combustible: ");
    Serial.print(combustible);
    Serial.println(" %");

    if (tiene_fix) {
      enviar_lectura(ultima_lat, ultima_lon, ultima_velocidad, combustible);
    } else {
      Serial.println("Sin fix de GPS todavia, se omite el envio");
    }

    ultimo_envio = millis();
  }

  delay(5);
}
