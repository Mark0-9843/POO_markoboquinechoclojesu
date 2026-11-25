#pragma once
#include "NodoIoT.h"
#include "NodoSensorFisico.h"

// Actuador de salida PWM (LED) que responde a la lectura de un sensor.
class NodoActuadorFisico : public NodoIoT {
private:                                  // encapsulamiento
    bool _estadoActivo;
    int _potenciaPwm;                     // 0 - 255
    bool _parpadeoEncendido;
    unsigned long _ultimoCambio;
    unsigned long _ultimoReporte;
    NodoSensorFisico* _sensor;            // sensor que gobierna al actuador

    void escribirSalida(int duty);        // unico punto que toca el hardware

public:
    NodoActuadorFisico(String id, int pinHardware);

    void iniciar() override;              // configura el canal PWM del LED
    void ejecutarAccion() override;       // conmuta la salida con ledcWrite()

    void vincularSensor(NodoSensorFisico* sensor);
    bool getEstadoActivo() const;
    int getPotenciaPwm() const;
};
