#include "DHT.h"

// ==========================================
// DEFINICIÓN DE PINES
// ==========================================
const int LDR_PIN = 32;   
const int DHT_PIN = 4;    
const int LED_PIN = 19;   

const int PWMA_PIN = 18; 
const int AIN1_PIN = 21; 
const int AIN2_PIN = 22; 
const int STBY_PIN = 23; 

// ==========================================
// CONFIGURACIÓN PWM (API ESP32 v3.0)
// ==========================================
const int frecuencia = 5000;   
const int resolucion = 8;      

#define DHTTYPE DHT11     
DHT dht(DHT_PIN, DHTTYPE);

// ==========================================
// VARIABLES GLOBALES DE ESTADO (Telemetría)
// ==========================================
int valorLDR = 0;
int brilloLED = 0;
int velocidadMotor = 0;
float temperatura = 0.0;
float humedad = 0.0;

// Variables de configuración del sistema
bool modoAutomatico = true; // true = sensores mandan, false = comandos manuales mandan
bool formatoJSON = false;   // true = salida JSON, false = salida en texto

// Control de tiempo para la telemetría (cada 2 segundos)
unsigned long tiempoAnteriorTelemetria = 0;
const long intervaloTelemetria = 2000;

// ==========================================
// SETUP
// ==========================================
void setup() {
  Serial.begin(115200);
  Serial.setTimeout(10); // Evita retrasos al leer comandos por Serial
  
  // Configurar puente H
  pinMode(AIN1_PIN, OUTPUT);
  pinMode(AIN2_PIN, OUTPUT);
  pinMode(STBY_PIN, OUTPUT);
  
  // Dirección constante y activación
  digitalWrite(AIN1_PIN, HIGH);
  digitalWrite(AIN2_PIN, LOW);
  digitalWrite(STBY_PIN, HIGH);

  // Configurar pines PWM
  ledcAttach(LED_PIN, frecuencia, resolucion);
  ledcAttach(PWMA_PIN, frecuencia, resolucion);
  
  dht.begin();
  Serial.println("Sistema de Instrumentación Iniciado.");
  Serial.println("Escriba 'FORMAT_JSON' para telemetria JSON o 'STATUS' para lectura instantanea.");
}

// ==========================================
// LOOP PRINCIPAL (Arquitectura limpia)
// ==========================================
void loop() {
  procesarComandos();
  leerSensores();
  
  if (modoAutomatico) {
    ejecutarLogicaAutomatica();
  }
  
  actualizarActuadores();
  
  // Emitir telemetría cada 2 segundos
  if (millis() - tiempoAnteriorTelemetria >= intervaloTelemetria) {
    tiempoAnteriorTelemetria = millis();
    imprimirTelemetria();
  }
}

// ==========================================
// FUNCIONES DEL SISTEMA
// ==========================================

void procesarComandos() {
  if (Serial.available() > 0) {
    String comando = Serial.readStringUntil('\n');
    comando.trim(); // Limpiar espacios ocultos o saltos de línea (\r)
    comando.toUpperCase(); // Hacerlo insensible a mayúsculas/minúsculas

    if (comando == "AUTO") {
      modoAutomatico = true;
    } 
    else if (comando == "MOTOR_ON") {
      modoAutomatico = false;
      velocidadMotor = 128;
    } 
    else if (comando == "MOTOR_OFF") {
      modoAutomatico = false;
      velocidadMotor = 0;
    } 
    else if (comando == "LED_ON") {
      modoAutomatico = false;
      brilloLED = 255;
    } 
    else if (comando == "LED_OFF") {
      modoAutomatico = false;
      brilloLED = 0;
    } 
    else if (comando == "FORMAT_JSON") {
      formatoJSON = true;
    } 
    else if (comando == "FORMAT_TEXT") {
      formatoJSON = false;
    } 
    else if (comando == "STATUS") {
      imprimirTelemetria(); // Imprime de inmediato
    } 
    else if (comando.length() > 0) {
      Serial.println("[ERROR] Comando desconocido.");
    }
  }
}

void leerSensores() {
  // LDR en tiempo real
  valorLDR = analogRead(LDR_PIN);
  
  // El DHT11 no debe leerse muy rápido, usamos el mismo temporizador de telemetría
  // para actualizar sus variables justo antes de imprimir
  if (millis() - tiempoAnteriorTelemetria >= (intervaloTelemetria - 10)) {
    float h = dht.readHumidity();
    float t = dht.readTemperature();
    // Solo actualizamos si la lectura es válida
    if (!isnan(h) && !isnan(t)) {
      humedad = h;
      temperatura = t;
    } else {
      temperatura = -999.0; // Código de error
      humedad = -999.0;
    }
  }
}

void ejecutarLogicaAutomatica() {
  // Lógica del LED
  brilloLED = map(valorLDR, 1000, 4095, 255, 0);
  brilloLED = constrain(brilloLED, 0, 255); 
  
  // Lógica del Motor / Ventilador
  if (temperatura > 30.0 && temperatura != -999.0) {
    velocidadMotor = 128; 
  } else {
    velocidadMotor = 0;   
  }
}

void actualizarActuadores() {
  ledcWrite(LED_PIN, brilloLED);
  ledcWrite(PWMA_PIN, velocidadMotor);
}

void imprimirTelemetria() {
  if (formatoJSON) {
    // Estructura JSON perfecta para integrarse con Python, C# o Web
    Serial.print("{\"modo\":\"");
    Serial.print(modoAutomatico ? "AUTO" : "MANUAL");
    Serial.print("\",\"temp\":");
    Serial.print(temperatura);
    Serial.print(",\"hum\":");
    Serial.print(humedad);
    Serial.print(",\"ldr\":");
    Serial.print(valorLDR);
    Serial.print(",\"pwm_led\":");
    Serial.print(brilloLED);
    Serial.print(",\"pwm_motor\":");
    Serial.print(velocidadMotor);
    Serial.println("}");
  } else {
    // Estructura de Texto Plano para diagnóstico visual
    Serial.print("[");
    Serial.print(modoAutomatico ? "AUTO" : "MANUAL");
    Serial.print("] Temp: ");
    if (temperatura == -999.0) Serial.print("ERR"); else { Serial.print(temperatura); Serial.print("C"); }
    Serial.print(" | Hum: ");
    if (humedad == -999.0) Serial.print("ERR"); else { Serial.print(humedad); Serial.print("%"); }
    Serial.print(" | LDR: "); Serial.print(valorLDR);
    Serial.print(" | LED: "); Serial.print(brilloLED);
    Serial.print(" | Motor: "); Serial.println(velocidadMotor);
  }
}
