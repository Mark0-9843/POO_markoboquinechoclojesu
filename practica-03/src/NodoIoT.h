#pragma once
#include <Arduino.h>

// Superclase base: datos y comportamiento comun de cualquier nodo fisico.
class NodoIoT {
protected:                       // visibles para las subclases, ocultos al exterior
    String idDispositivo;
    int pin;
    bool conectado;

public:
    NodoIoT(String id, int pinHardware);
    virtual ~NodoIoT() {}        // destructor virtual: libera bien objetos por puntero base

    virtual void iniciar();                 // configura el nodo (las hijas lo extienden)
    virtual void ejecutarAccion() = 0;      // metodo polimorfico PURO: cada hija lo implementa

    String getId() const;
    int getPin() const;
    bool estaConectado() const;
};
