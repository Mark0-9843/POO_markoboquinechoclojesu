#include <Arduino.h> // Librería principal para el framework de Arduino

// Pines asignados a cada periférico
const int PIN_TEMP = 34;   // Entrada analógica (ADC) para sensor LM35
const int PIN_LDR = 32;    // Entrada analógica (ADC) para la fotorresistencia
const int PIN_FAN = 18;    // Salida PWM hacia el driver del ventilador
const int PIN_LED = 19;    // Salida PWM hacia el driver/transistor del LED

// Parámetros para el periférico LEDC (PWM del ESP32)
const int FREQ_PWM = 5000;    // Frecuencia de conmutación a 5 kHz
const int RESOLUTION = 8;     // Resolución de 8 bits (rango 0 a 255)
const int CHANNEL_FAN = 0;    // Canal PWM 0 dedicado al ventilador
const int CHANNEL_LED = 1;    // Canal PWM 1 dedicado al LED

// Control de tiempo sin delay()
unsigned long lastMillis = 0; // Guarda la marca de tiempo de la última telemetría
const long interval = 2000;   // Tiempo de espera entre envíos (2 segundos)

void setup() {
  Serial.begin(115200); // Inicia comunicación serie a 115200 baudios

  // Configuración de pines de entrada
  pinMode(PIN_TEMP, INPUT); // Configura pin de temperatura como entrada
  pinMode(PIN_LDR, INPUT);  // Configura pin del LDR como entrada
  analogSetAttenuation(ADC_11db); // Escala el ADC para medir hasta ~3.3V

  // Inicializa y asocia el PWM del ventilador
  ledcSetup(CHANNEL_FAN, FREQ_PWM, RESOLUTION); // Configura frecuencia y resolución en canal 0
  ledcAttachPin(PIN_FAN, CHANNEL_FAN);          // Asigna el pin 18 al canal 0

  // Inicializa y asocia el PWM del LED
  ledcSetup(CHANNEL_LED, FREQ_PWM, RESOLUTION); // Configura frecuencia y resolución en canal 1
  ledcAttachPin(PIN_LED, CHANNEL_LED);          // Asigna el pin 19 al canal 1

  // Seguridad: arranca ambos actuadores apagados (duty cycle en 0)
  ledcWrite(CHANNEL_FAN, 0); // Apaga ventilador
  ledcWrite(CHANNEL_LED, 0); // Apaga LED
}

void loop() {
  // --- 1. Lectura y conversión de sensores ---
  int rawTemp = analogRead(PIN_TEMP); // Lee valor crudo del ADC (0 a 4095)
  // Conversión a voltios y luego a °C (LM35 entrega 10mV/°C)
  float temperatura = (rawTemp * 3.3 / 4095.0) * 100.0; 

  int ldrValue = analogRead(PIN_LDR); // Lee nivel de luz crudo (0 a 4095)

  // --- 2. Lógica de control ---
  // Control ON/OFF para ventilador según umbral de temperatura
  if (temperatura > 30.0) {
    ledcWrite(CHANNEL_FAN, 255); // Si supera 30°C, ventilador a máxima potencia
  } else {
    ledcWrite(CHANNEL_FAN, 0);   // Si baja de 30°C, se apaga
  }

  // Control proporcional inverso: a menos luz ambiental, más potencia en el LED
  int ledPWM = map(ldrValue, 0, 4095, 255, 0); // Invierte la escala de 12 bits a 8 bits
  ledPWM = constrain(ledPWM, 0, 255);          // Limita el valor para evitar desbordes
  ledcWrite(CHANNEL_LED, ledPWM);              // Aplica el ciclo de trabajo al LED

  // --- 3. Comandos por consola serie ---
  if (Serial.available() > 0) { // Revisa si hay bytes en el buffer serie
    String command = Serial.readStringUntil('\n'); // Lee el comando hasta el salto de línea
    command.trim(); // Elimina espacios o caracteres \r sobrantes
    
    // Procesa el comando ingresado
    if (command.equalsIgnoreCase("STATUS")) { // Pide lectura manual bajo demanda
      enviarTelemetriaJSON(temperatura, ldrValue, ledPWM, (temperatura > 30.0 ? 255 : 0));
    } else if (command.equalsIgnoreCase("HELP")) { // Muestra opciones disponibles
      Serial.println(F("Comandos disponibles: STATUS (Muestra telemetria en JSON)"));
    }
  }

  // --- 4. Envío periódico no bloqueante ---
  if (millis() - lastMillis >= interval) { // Comprueba si ya pasaron los 2 segundos
    lastMillis = millis(); // Actualiza la marca de tiempo
    enviarTelemetriaJSON(temperatura, ldrValue, ledPWM, (temperatura > 30.0 ? 255 : 0)); // Envía paquete JSON
  }
}

// Función auxiliar para formatear y transmitir datos en formato JSON
void enviarTelemetriaJSON(float temp, int ldr, int fanPWM, int statusFan) {
  Serial.print("{"); // Abre estructura JSON
  Serial.print("\"temperatura_C\":"); Serial.print(temp, 2); // Imprime temperatura con 2 decimales
  Serial.print(",\"ldr_raw\":"); Serial.print(ldr);          // Imprime valor ADC del LDR
  Serial.print(",\"led_pwm\":"); Serial.print(fanPWM);       // Imprime valor PWM del LED (parámetro fanPWM)
  Serial.print(",\"fan_pwm\":"); Serial.print(statusFan);     // Imprime estado PWM del ventilador
  Serial.println("}"); // Cierra estructura JSON con salto de línea
}

