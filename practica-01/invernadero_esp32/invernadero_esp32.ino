#include <Arduino.h>

/* ============================================================
 *  Sistema de control físico ESP32
 *  - Gestión térmica: ventilador a PWM 100 % si T > 30 °C
 *  - Gestión lumínica: LED con control proporcional inverso al LDR
 *  - PWM con periférico LEDC (ledcSetup / ledcAttachPin / ledcWrite)
 *  Compatible con Arduino-ESP32 core 2.x
 * ============================================================ */

// ---------- Asignación estricta de pines ----------
constexpr uint8_t PIN_TEMP = 34;  // ADC  - LM35 (12 bits)
constexpr uint8_t PIN_LDR  = 32;  // ADC  - Fotorresistencia
constexpr uint8_t PIN_FAN  = 18;  // PWM  - Ventilador (motor DC)
constexpr uint8_t PIN_LED  = 19;  // PWM  - LED de potencia

// ---------- Configuración PWM (LEDC) ----------
constexpr uint32_t PWM_FREQ = 5000;                 // 5 kHz
constexpr uint8_t  PWM_RES  = 8;                    // 8 bits -> 0..255
constexpr uint8_t  PWM_MAX  = (1 << PWM_RES) - 1;   // 255 = 100 %
constexpr uint8_t  CH_FAN   = 0;
constexpr uint8_t  CH_LED   = 1;

// ---------- Parámetros de control ----------
constexpr float    TEMP_UMBRAL = 30.0f;  // °C: enciende el ventilador
constexpr float    TEMP_HISTER = 1.0f;   // °C: apaga a (umbral - histéresis)
constexpr uint8_t  ADC_MUESTRAS = 16;    // Promediado para reducir ruido
constexpr uint32_t CONTROL_MS   = 100;   // Periodo del lazo de control
constexpr uint32_t TELEMETRIA_MS = 2000; // Periodo de telemetría periódica

// ---------- Estado del sistema ----------
struct Estado {
  float   temperaturaC = 0.0f;
  int     ldrRaw       = 0;
  uint8_t ledPwm       = 0;
  uint8_t fanPwm       = 0;
} estado;

uint32_t ultimoControl    = 0;
uint32_t ultimaTelemetria = 0;

// ---------- Prototipos ----------
uint32_t leerPromedioRaw(uint8_t pin);
uint32_t leerPromedioMv(uint8_t pin);
void actualizarControl();
void procesarSerial();
void ejecutarComando(String &cmd);
void enviarTelemetriaJSON();

// ============================================================
void setup() {
  Serial.begin(115200);
  Serial.setTimeout(20);

  // Entradas analógicas. El LM35 entrega 10 mV/°C (300 mV a 30 °C), por lo
  // que se usa atenuación 0 dB (~0-950 mV) para ganar resolución y linealidad.
  pinMode(PIN_TEMP, INPUT);
  pinMode(PIN_LDR, INPUT);
  analogSetPinAttenuation(PIN_TEMP, ADC_0db);
  analogSetPinAttenuation(PIN_LDR, ADC_11db);   // LDR: rango completo ~3.3 V

  // Canal PWM del ventilador
  ledcSetup(CH_FAN, PWM_FREQ, PWM_RES);
  ledcAttachPin(PIN_FAN, CH_FAN);

  // Canal PWM del LED de potencia
  ledcSetup(CH_LED, PWM_FREQ, PWM_RES);
  ledcAttachPin(PIN_LED, CH_LED);

  // Seguridad: actuadores apagados al arrancar
  ledcWrite(CH_FAN, 0);
  ledcWrite(CH_LED, 0);

  actualizarControl();  // Primera lectura para que STATUS no devuelva ceros
}

// ============================================================
void loop() {
  const uint32_t ahora = millis();

  // 1. Lazo de control a periodo fijo (no bloqueante)
  if (ahora - ultimoControl >= CONTROL_MS) {
    ultimoControl = ahora;
    actualizarControl();
  }

  // 2. Comandos por consola serie (no bloqueante)
  procesarSerial();

  // 3. Telemetría periódica
  if (ahora - ultimaTelemetria >= TELEMETRIA_MS) {
    ultimaTelemetria = ahora;
    enviarTelemetriaJSON();
  }
}

// ============================================================
//  Lectura y control
// ============================================================

// Promedio de N muestras crudas (0-4095)
uint32_t leerPromedioRaw(uint8_t pin) {
  uint32_t suma = 0;
  for (uint8_t i = 0; i < ADC_MUESTRAS; i++) suma += analogRead(pin);
  return suma / ADC_MUESTRAS;
}

// Promedio de N muestras en mV (usa la calibración de fábrica del ESP32)
uint32_t leerPromedioMv(uint8_t pin) {
  uint32_t suma = 0;
  for (uint8_t i = 0; i < ADC_MUESTRAS; i++) suma += analogReadMilliVolts(pin);
  return suma / ADC_MUESTRAS;
}

void actualizarControl() {
  // --- Sensores ---
  estado.temperaturaC = leerPromedioMv(PIN_TEMP) / 10.0f;  // 10 mV por °C
  estado.ldrRaw       = leerPromedioRaw(PIN_LDR);

  // --- Gestión térmica: ON/OFF con histéresis ---
  // Enciende por encima de 30 °C y apaga por debajo de 29 °C,
  // evitando que el ventilador oscile alrededor del umbral.
  if (estado.temperaturaC > TEMP_UMBRAL) {
    estado.fanPwm = PWM_MAX;                                // 100 %
  } else if (estado.temperaturaC < (TEMP_UMBRAL - TEMP_HISTER)) {
    estado.fanPwm = 0;
  }
  ledcWrite(CH_FAN, estado.fanPwm);

  // --- Gestión lumínica: control proporcional inverso ---
  // 4095 >> 4 = 255, por lo que menos luz (LDR bajo) => más duty en el LED.
  estado.ledPwm = PWM_MAX - (estado.ldrRaw >> 4);
  ledcWrite(CH_LED, estado.ledPwm);
}

// ============================================================
//  Consola serie
// ============================================================

void procesarSerial() {
  static String buffer;
  while (Serial.available() > 0) {
    const char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (buffer.length() > 0) {
        ejecutarComando(buffer);
        buffer = "";
      }
    } else if (buffer.length() < 32) {
      buffer += c;
    }
  }
}

void ejecutarComando(String &cmd) {
  cmd.trim();
  if (cmd.equalsIgnoreCase("STATUS")) {
    enviarTelemetriaJSON();
  } else if (cmd.equalsIgnoreCase("HELP")) {
    Serial.println(F("Comandos disponibles: STATUS (telemetria en JSON), HELP"));
  } else {
    Serial.println(F("Comando desconocido. Escribe HELP"));
  }
}

// ============================================================
//  Telemetría
// ============================================================

void enviarTelemetriaJSON() {
  Serial.printf(
    "{\"temperatura_C\":%.2f,\"ldr_raw\":%d,\"led_pwm\":%u,\"fan_pwm\":%u}\n",
    estado.temperaturaC, estado.ldrRaw, estado.ledPwm, estado.fanPwm);
}
