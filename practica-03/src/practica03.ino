#include "NodoIoT.h"
#include "NodoSensorFisico.h"
#include "NodoActuadorFisico.h"

// ----- Hardware -----
const int PIN_POT = 34;      // Potenciometro (entrada analogica ADC1)
const int PIN_LED = 23;      // LED con resistencia de 220 ohm (salida PWM)

// ----- Red IoT: arreglo de punteros a la superclase -----
const int N = 2;
NodoIoT* red[N];

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("=== Practica 3: Nodos IoT heterogeneos (ESP32) ===");

    NodoSensorFisico*   sensor   = new NodoSensorFisico("SENS_POT", PIN_POT, 3000);
    NodoActuadorFisico* actuador = new NodoActuadorFisico("ACT_LED", PIN_LED);
    actuador->vincularSensor(sensor);     // el LED responde al potenciometro

    red[0] = sensor;                      // el sensor se ejecuta antes que el actuador
    red[1] = actuador;

    for (int i = 0; i < N; i++) {
        red[i]->iniciar();
    }
}

void loop() {
    // Bucle polimorfico: no se pregunta de que tipo es cada nodo
    for (int i = 0; i < N; i++) {
        red[i]->ejecutarAccion();
    }
    delay(20);
}
