# Simulador de Reactor en Python - Versión 1.0.0

Este proyecto corresponde a la primera parte de la práctica (Sección 1.0.0). Se requiere la creación de un sistema dinámico de lazo cerrado que modela el comportamiento térmico y barométrico de un reactor químico, implementado en Python haciendo uso de Programación Orientada a Objetos (POO).

## Especificaciones de Hardware Simulado

El sistema simula periféricos industriales abstraídos a través de clases de Python (`Sensor` y `Actuador`). Las especificaciones de los dispositivos son las siguientes:

| Periférico | Variable | Rango de Operación | Método de Control |
| :--- | :--- | :--- | :--- |
| **Sensor** | Temperatura | 0 - 150.0 °C | Muestreo Analógico |
| **Sensor** | Presión | 0 - 15.0 Bar | Muestreo Analógico |
| **Actuador** | Bomba de Enfriamiento | 0 - 100 % | Modulación Proporcional |
| **Actuador** | Válvula de Alivio | Digital (0/1) | Control ON/OFF |

## Diagrama de Clases (UML)

A continuación se presenta la arquitectura de software del sistema, modelada mediante Programación Orientada a Objetos (POO). Se detalla la relación de herencia para los actuadores (proporcionales y digitales) y la estructura encapsulada del sensor:

```text
               [ HERENCIA DE ACTUADORES ]                                       [ CLASE INDEPENDIENTE ]

                      +------------------------+                       +-----------------------------------------------+
                      |        Actuador        |                       |                    Sensor                     |
                      +------------------------+                       +-----------------------------------------------+
                      | - nombre: str          |                       | - nombre: str                                 |
                      | - estado: bool = False |                       | - variable_fisica: str                        |
                      +------------------------+                       | - rango_min: float                            |
                      | + __init__(nombre: str)|                       | - rango_max: float                            |
                      | + encender(): void     |                       | - sensibilidad: float                         |
                      | + apagar(): void       |                       | - decimales_medicion: int                     |
                      +-----------+------------+                       | - unidad: str                                 |
                                  ^                                    | - valor_actual: float                         |
               +------------------+------------------+                 +-----------------------------------------------+
               |                                     |                 | + __init__(nom, var, min, max, sn, dec, und)  |
 +-----------------------------+       +-----------------------------+ | + leer_valor_actual(): float                  |
 |    ActuadorProporcional     |       |       ActuadorDigital       | | + info(): str                                 |
 +-----------------------------+       +-----------------------------+ +-----------------------------------------------+
 | - rango_operacion_min: float|       | - punto_operacion: int = 0  |
 | - rango_operacion_max: float|       +-----------------------------+
 | - punto_operacion: float    |       | + __init__(nombre: str)     |
 +-----------------------------+       | + encender(): void          |
 | + __init__(nombre: str)     |       | + apagar(): void            |
 | + ajustar(valor: float):void|       | + ajustar(valor: float):void|
 | + info(): str               |       | + info(): str               |
 +-----------------------------+       +-----------------------------+
```
Lógica de los Modos de Operación
El comportamiento del sistema se rige bajo tres modos fundamentales:

Modo Manual: Interacción directa por consola (HMI estático). El operario define los comandos de estado de los actuadores (ej. encender, apagar, ajustar).

Modo Automático: Implementación del algoritmo de estabilidad dinámico del reactor basado en la siguiente fórmula:

ΔT = (+1.5°C) - (0.05°C × % OperaciónBomba)

Modo de Pruebas: Rutina de inyección de fallos destinada a la validación de los límites operativos del sistema.

[!WARNING]
Interlocks de Seguridad (Prioridad de Ejecución):
Si en cualquier momento la Temperatura > 85.0 °C o la Presión > 12.0 Bar, el sistema ignorará inmediatamente cualquier instrucción del operario y forzará de manera simultánea:

La Bomba de Enfriamiento al 100%.

La Apertura Total de la Válvula de Alivio.

Nota: Dentro de la consola, puedes usar comandos como encender, apagar o ajustar seguido del nombre del equipo, y escribir terminar para salir de manera segura.
