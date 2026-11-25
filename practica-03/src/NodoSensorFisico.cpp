#include "NodoSensorFisico.h"

static const int ADC_MAX = 4095;                      // 12 bits en el ESP32
static const unsigned long INTERVALO_REPORTE = 500;   // ms entre reportes por Serial

// Se invoca al constructor del padre en la lista de inicializacion (equivale a super())
NodoSensorFisico::NodoSensorFisico(String id, int pinHardware, int umbralAlerta)
    : NodoIoT(id, pinHardware),
      _umbralAlerta(ADC_MAX),
      _ultimaLectura(0),
      _alertaPrevia(false),
      _ultimoReporte(0) {
    setUmbralAlerta(umbralAlerta);            // el valor inicial tambien pasa por la validacion
}

bool NodoSensorFisico::setUmbralAlerta(int valor) {
    if (valor < 0 || valor > ADC_MAX) {
        Serial.print("[ERROR] ");
        Serial.print(idDispositivo);
        Serial.print(": umbral ");
        Serial.print(valor);
        Serial.println(" fuera del rango del ADC (0 - 4095). No se modifica.");
        return false;
    }
    _umbralAlerta = valor;
    return true;
}

int NodoSensorFisico::getUmbralAlerta() const { return _umbralAlerta; }
int NodoSensorFisico::getUltimaLectura() const { return _ultimaLectura; }
bool NodoSensorFisico::enAlerta() const { return _ultimaLectura >= _umbralAlerta; }

void NodoSensorFisico::iniciar() {
    pinMode(pin, INPUT);
    analogSetPinAttenuation(pin, ADC_11db);   // rango de lectura 0 - 3.3 V
    NodoIoT::iniciar();                       // reutiliza el comportamiento del padre
}

void NodoSensorFisico::ejecutarAccion() {
    _ultimaLectura = analogRead(pin);

    // Evento: cambio de estado de alerta
    bool alerta = enAlerta();
    if (alerta != _alertaPrevia) {
        _alertaPrevia = alerta;
        Serial.print("[EVENTO] ");
        Serial.print(idDispositivo);
        Serial.println(alerta ? ": ALERTA activada (umbral superado)" : ": lectura normalizada");
    }

    // Lectura periodica por el Monitor Serie
    unsigned long ahora = millis();
    if (ahora - _ultimoReporte >= INTERVALO_REPORTE) {
        _ultimoReporte = ahora;
        float voltaje = _ultimaLectura * 3.3f / ADC_MAX;
        Serial.print("[");
        Serial.print(idDispositivo);
        Serial.print("] ADC: ");
        Serial.print(_ultimaLectura);
        Serial.print(" (");
        Serial.print(_ultimaLectura * 100 / ADC_MAX);
        Serial.print("%) | ");
        Serial.print(voltaje, 2);
        Serial.print(" V | Umbral: ");
        Serial.println(_umbralAlerta);
    }
}
