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
## Lógica de los Modos de Operación

El comportamiento del sistema se rige bajo tres modos fundamentales:

1. **Modo Manual:** Interacción directa por consola (HMI estático). El operario define los comandos de estado de los actuadores (ej. `encender`, `apagar`, `ajustar`).
2. **Modo Automático:** Implementación del algoritmo de estabilidad dinámico del reactor basado en la siguiente fórmula:
   > `ΔT = (+1.5°C) - (0.05°C × % OperaciónBomba)`
3. **Modo de Pruebas:** Rutina de inyección de fallos destinada a la validación de los límites operativos del sistema.

> [!WARNING]
> **Interlocks de Seguridad (Prioridad de Ejecución):**
> Si en cualquier momento la **Temperatura > 85.0 °C** o la **Presión > 12.0 Bar**, el sistema ignorará inmediatamente cualquier instrucción del operario y forzará de manera simultánea:
> * La **Bomba de Enfriamiento al 100%**.
> * La **Apertura Total de la Válvula de Alivio**.

*Nota: Dentro de la consola, puedes usar comandos como `encender`, `apagar` o `ajustar` seguido del nombre del equipo, y escribir `terminar` para salir de manera segura.*

## Versión 2.0.0: Portafolio Físico en Hardware (ESP32 en C++)

Esta versión corresponde a la implementación de un Micro-Invernadero Inteligente mediante control por microcontrolador[cite: 4]. El código está desarrollado en C++ para la plataforma ESP32 y se encarga de la gestión automatizada de variables físicas junto con una interfaz de comandos por consola.

### Configuración de Pines

La asignación de periféricos al microcontrolador se define de la siguiente manera, basándose en la implementación del código y las especificaciones técnicas requeridas:

*   **Sensor Térmico (DHT11):** GPIO 4 *(Nota: Modificado en código respecto a la especificación original para adecuarse al hardware físico)*.
*   **Sensor LDR:** GPIO 32 para lectura de luz ambiental mediante ADC[cite: 4].
*   **Ventilador (Motor DC):** GPIO 18 configurado como salida PWM a una frecuencia de 5kHz[cite: 4]. Adicionalmente, el código implementa el control de un Puente H a través de los pines GPIO 21 (AIN1), 22 (AIN2) y 23 (STBY).
*   **LED de Potencia:** GPIO 19 configurado como salida PWM[cite: 4].

### Algoritmo de Control Físico

El sistema opera mediante un bucle principal (Loop) que ejecuta la lógica de estabilización cuando se encuentra en `Modo Automático`:

*   **Gestión Térmica:** Activación del ventilador si la temperatura excede los 30 °C[cite: 4]. En el código, esto se traduce en una señal PWM con valor de 128 (aprox. 50% del *Duty Cycle* a 8 bits).
*   **Gestión Lumínica:** El sistema compensa la falta de luz natural[cite: 4]. Utilizando la función `map()`, a menor valor registrado en el LDR, mayor es el *Duty Cycle* del LED de potencia, logrando un control proporcional[cite: 4].
*   **Implementación PWM:** Se utilizan las funciones actualizadas de la API de ESP32 v3.0 (`ledcAttach` y `ledcWrite`) a 8 bits de resolución y 5kHz de frecuencia.

### Comunicación Serial y Telemetría

El sistema debe procesar comandos desde el Monitor Serie para permitir el diagnóstico manual y la lectura de telemetría en formato JSON o texto plano estructurado[cite: 4]. El ESP32 emite reportes periódicos cada 2 segundos.

**Comandos de Consola Disponibles:**
*   `AUTO`: Retorna el sistema al control basado en sensores.
*   `MOTOR_ON` / `MOTOR_OFF`: Permite forzar el encendido/apagado del motor (cambia el sistema a modo manual automáticamente).
*   `LED_ON` / `LED_OFF`: Permite forzar el encendido/apagado del LED (cambia el sistema a modo manual automáticamente).
*   `FORMAT_JSON`: Cambia la estructura de los datos emitidos a un formato JSON compatible con integraciones de software.
*   `FORMAT_TEXT`: Cambia la estructura a un formato de texto plano para diagnóstico visual.
*   `STATUS`: Imprime la telemetría actual de manera instantánea, sin esperar el intervalo de 2 segundos.
