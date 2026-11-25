#pragma once
#include "NodoIoT.h"

// Sensor analogico (potenciometro) conectado a un pin ADC del ESP32.
class NodoSensorFisico : public NodoIoT {
private:                                  // encapsulamiento
    int _umbralAlerta;                    // 0 - 4095 (ADC de 12 bits)
    int _ultimaLectura;
    bool _alertaPrevia;
    unsigned long _ultimoReporte;

public:
    NodoSensorFisico(String id, int pinHardware, int umbralAlerta);

    void iniciar() override;              // configura el pin como entrada analogica
    void ejecutarAccion() override;       // lee con analogRead() y reporta por Serial

    bool setUmbralAlerta(int valor);      // setter: valida el rango del ADC
    int getUmbralAlerta() const;
    int getUltimaLectura() const;
    bool enAlerta() const;
};
