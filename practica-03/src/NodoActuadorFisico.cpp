#include "NodoActuadorFisico.h"

static const int PWM_FRECUENCIA = 5000;          // Hz
static const int PWM_RESOLUCION = 8;             // bits -> 0 - 255
static const int PWM_MAX = 255;
static const int PWM_CANAL = 0;                  // solo se usa con el core 2.x
static const unsigned long PERIODO_PARPADEO = 100;    // ms
static const unsigned long INTERVALO_REPORTE = 500;   // ms

// Core 3.x de Arduino-ESP32 cambio la API de ledc; se soportan ambas versiones
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  #define PWM_CONFIGURAR(pin)      ledcAttach(pin, PWM_FRECUENCIA, PWM_RESOLUCION)
  #define PWM_ESCRIBIR(pin, duty)  ledcWrite(pin, duty)
#else
  #define PWM_CONFIGURAR(pin)      do { ledcSetup(PWM_CANAL, PWM_FRECUENCIA, PWM_RESOLUCION); ledcAttachPin(pin, PWM_CANAL); } while (0)
  #define PWM_ESCRIBIR(pin, duty)  ledcWrite(PWM_CANAL, duty)
#endif

NodoActuadorFisico::NodoActuadorFisico(String id, int pinHardware)
    : NodoIoT(id, pinHardware),
      _estadoActivo(false),
      _potenciaPwm(0),
      _parpadeoEncendido(false),
      _ultimoCambio(0),
      _ultimoReporte(0),
      _sensor(nullptr) {}

void NodoActuadorFisico::vincularSensor(NodoSensorFisico* sensor) { _sensor = sensor; }
bool NodoActuadorFisico::getEstadoActivo() const { return _estadoActivo; }
int NodoActuadorFisico::getPotenciaPwm() const { return _potenciaPwm; }

void NodoActuadorFisico::iniciar() {
    PWM_CONFIGURAR(pin);
    escribirSalida(0);                    // arranca apagado
    NodoIoT::iniciar();
}

void NodoActuadorFisico::escribirSalida(int duty) {
    _potenciaPwm = constrain(duty, 0, PWM_MAX);
    _estadoActivo = _potenciaPwm > 0;
    PWM_ESCRIBIR(pin, _potenciaPwm);
}

void NodoActuadorFisico::ejecutarAccion() {
    if (_sensor == nullptr) return;       // sin sensor vinculado no hay nada que obedecer

    unsigned long ahora = millis();
    if (_sensor->enAlerta()) {
        // Alerta: el LED parpadea a maxima potencia
        if (ahora - _ultimoCambio >= PERIODO_PARPADEO) {
            _ultimoCambio = ahora;
            _parpadeoEncendido = !_parpadeoEncendido;
        }
        escribirSalida(_parpadeoEncendido ? PWM_MAX : 0);
    } else {
        // Normal: brillo proporcional a la lectura del potenciometro
        _parpadeoEncendido = false;
        escribirSalida(map(_sensor->getUltimaLectura(), 0, 4095, 0, PWM_MAX));
    }

    if (ahora - _ultimoReporte >= INTERVALO_REPORTE) {
        _ultimoReporte = ahora;
        Serial.print("[");
        Serial.print(idDispositivo);
        Serial.print("] Estado: ");
        Serial.print(_estadoActivo ? "ON" : "OFF");
        Serial.print(" | PWM: ");
        Serial.print(_potenciaPwm);
        Serial.print("/");
        Serial.println(PWM_MAX);
    }
}
