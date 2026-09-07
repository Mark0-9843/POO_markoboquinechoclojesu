#include <Arduino.h>

// Definición estricta de pines
const int PIN_TEMP = 34;   // Sensor Térmico (ADC)
const int PIN_LDR = 32;    // Sensor LDR (ADC)
const int PIN_FAN = 18;    // Ventilador (PWM)
const int PIN_LED = 19;    // LED de Potencia (PWM)

// Configuración de canales PWM 
const int FREQ_PWM = 5000;    // Frecuencia de 5 kHz
const int RESOLUTION = 8;     // Resolución de 8 bits (0 - 255)
const int CHANNEL_FAN = 0;    // Canal PWM para ventilador
const int CHANNEL_LED = 1;    // Canal PWM para LED

unsigned long lastMillis = 0;
const long interval = 2000;   // Intervalo de telemetría (2 segundos)

void setup() {
  Serial.begin(115200);

  // Configuración de entradas analógicas 
  pinMode(PIN_TEMP, INPUT);
  pinMode(PIN_LDR, INPUT);
  analogSetAttenuation(ADC_11db); // Rango completo de 0 a 3.3V

  // Configuración de periféricos PWM (ledc)
  ledcSetup(CHANNEL_FAN, FREQ_PWM, RESOLUTION);
  ledcAttachPin(PIN_FAN, CHANNEL_FAN);

  ledcSetup(CHANNEL_LED, FREQ_PWM, RESOLUTION);
  ledcAttachPin(PIN_LED, CHANNEL_LED);

  // Estado inicial apagado
  ledcWrite(CHANNEL_FAN, 0);
  ledcWrite(CHANNEL_LED, 0);
}

void loop() {
  // 1. Lectura de Sensores
  int rawTemp = analogRead(PIN_TEMP);
  // Conversión aproximada para LM35 (Voltaje a Temperatura: (raw / 4095) * 3.3V * 100)
  float temperatura = (rawTemp * 3.3 / 4095.0) * 100.0; 

  int ldrValue = analogRead(PIN_LDR); // Rango 0 - 4095

  // 2. Algoritmo de Control Físico
  // Gestión Térmica: Ventilador al 100% si > 30°C
  if (temperatura > 30.0) {
    ledcWrite(CHANNEL_FAN, 255); // 100% Duty Cycle
  } else {
    ledcWrite(CHANNEL_FAN, 0);   // Apagado
  }

  // Gestión Lumínica: Control proporcional inverso
  // A menor luz (LDR bajo), mayor intensidad del LED
  int ledPWM = map(ldrValue, 0, 4095, 255, 0);
  ledPWM = constrain(ledPWM, 0, 255);
  ledcWrite(CHANNEL_LED, ledPWM);

  // 3. Procesamiento de Comandos Seriales (Diagnóstico Manual)
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.equalsIgnoreCase("STATUS")) {
      enviarTelemetriaJSON(temperatura, ldrValue, ledPWM, (temperatura > 30.0 ? 255 : 0));
    } else if (command.equalsIgnoreCase("HELP")) {
      Serial.println(F("Comandos disponibles: STATUS (Muestra telemetria en JSON)"));
    }
  }

  // 4. Telemetría Periódica Automática (JSON)
  if (millis() - lastMillis >= interval) {
    lastMillis = millis();
    enviarTelemetriaJSON(temperatura, ldrValue, ledPWM, (temperatura > 30.0 ? 255 : 0));
  }
}

void enviarTelemetriaJSON(float temp, int ldr, int fanPWM, int statusFan) {
  Serial.print("{");
  Serial.print("\"temperatura_C\":"); Serial.print(temp, 2);
  Serial.print(",\"ldr_raw\":"); Serial.print(ldr);
  Serial.print(",\"led_pwm\":"); Serial.print(fanPWM);
  Serial.print(",\"fan_pwm\":"); Serial.print(statusFan);
  Serial.println("}");
}
