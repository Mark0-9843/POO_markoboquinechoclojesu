#include "NodoIoT.h"

// Lista de inicializacion: construye los atributos antes de entrar al cuerpo
NodoIoT::NodoIoT(String id, int pinHardware)
    : idDispositivo(id), pin(pinHardware), conectado(false) {}

void NodoIoT::iniciar() {
    conectado = true;
    Serial.print("[RED] ");
    Serial.print(idDispositivo);
    Serial.print(" conectado en pin ");
    Serial.println(pin);
}

String NodoIoT::getId() const { return idDispositivo; }
int NodoIoT::getPin() const { return pin; }
bool NodoIoT::estaConectado() const { return conectado; }
