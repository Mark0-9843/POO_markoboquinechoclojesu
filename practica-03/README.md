# Práctica 3: Implementación física de nodos IoT heterogéneos en C++ (ESP32)

Esta práctica traslada la arquitectura jerárquica diseñada en Python (Práctica 2) a hardware real con un **ESP32** y **C++**, aplicando los tres pilares de la programación orientada a objetos: **herencia, encapsulamiento y polimorfismo**.

## Descripción general

Se simula una pequeña red IoT con dos nodos físicos de distinto tipo que se gestionan de forma uniforme mediante un arreglo de punteros a la superclase:

| Nodo | Clase | Hardware | Función |
|------|-------|----------|---------|
| `SENS_POT` | `NodoSensorFisico` | Potenciómetro en GPIO 34 (ADC) | Lee el valor analógico y detecta la condición de alerta |
| `ACT_LED` | `NodoActuadorFisico` | LED con resistencia de 220 Ω en GPIO 23 (PWM) | Responde a la lectura del sensor |

### Comportamiento

- **Modo normal:** el brillo del LED es proporcional a la posición del potenciómetro (`map()` de 0-4095 a 0-255).
- **Modo alerta:** cuando la lectura del ADC es mayor o igual al umbral (**3000**, aproximadamente 2.4 V), el LED parpadea a máxima potencia (periodo de 100 ms).
- **Monitor Serie (115200 baudios):** se reportan las lecturas cada 500 ms y los eventos de cambio de estado de alerta.

## Estructura del repositorio

```
/
├── .gitignore
├── AUTHORS
└── practica-03/
    ├── src/
    │   ├── practica03.ino
    │   ├── NodoIoT.h
    │   ├── NodoIoT.cpp
    │   ├── NodoSensorFisico.h
    │   ├── NodoSensorFisico.cpp
    │   ├── NodoActuadorFisico.h
    │   └── NodoActuadorFisico.cpp
    └── docs/
        └── Reporte_Evidencias_P3.pdf
```

## Diseño orientado a objetos

```
            NodoIoT  (abstracta)
            ├── idDispositivo, pin, conectado   (protected)
            ├── virtual iniciar()
            └── virtual ejecutarAccion() = 0    (polimórfico puro)
               ▲                    ▲
               │                    │
     NodoSensorFisico      NodoActuadorFisico
```

### Herencia
`NodoSensorFisico` y `NodoActuadorFisico` heredan de `NodoIoT` y llaman al constructor del padre mediante **lista de inicialización** (equivalente a `super()`). Ambas reutilizan `NodoIoT::iniciar()` dentro de su propio `iniciar()`.

### Encapsulamiento
- `NodoSensorFisico`: el umbral `_umbralAlerta` es **privado**. Solo se modifica con `setUmbralAlerta()`, que valida el rango del ADC del ESP32 (0 a 4095) y rechaza valores inválidos.
- `NodoActuadorFisico`: `_estadoActivo` y `_potenciaPwm` son **privados**. El acceso al hardware se concentra en un único método privado, `escribirSalida()`.

### Polimorfismo
Cada subclase sobrescribe `ejecutarAccion()`:
- El sensor lee con `analogRead()` y reporta por el puerto serie.
- El actuador conmuta la salida con `ledcWrite()` (PWM) según el estado del sensor vinculado.

El `loop()` recorre el arreglo sin preguntar el tipo de cada nodo:

```cpp
NodoIoT* red[N];

void loop() {
    for (int i = 0; i < N; i++) {
        red[i]->ejecutarAccion();
    }
    delay(20);
}
```

## Hardware necesario

- 1 × ESP32 (placa de desarrollo)
- 1 × potenciómetro (por ejemplo, 10 kΩ)
- 1 × LED
- 1 × resistencia de 220 Ω
- 1 × protoboard y cables jumper
- Cable USB para programar y alimentar

## Conexiones

| Componente | Conexión |
|------------|----------|
| Potenciómetro, terminal 1 | 3V3 |
| Potenciómetro, terminal central (cursor) | GPIO 34 |
| Potenciómetro, terminal 3 | GND |
| LED (ánodo, pata larga) | GPIO 23 mediante resistencia de 220 Ω |
| LED (cátodo, pata corta) | GND |

> El diagrama esquemático y las fotografías del montaje están en `docs/Reporte_Evidencias_P3.pdf`.

## Cómo compilar y cargar

1. Instala el soporte de ESP32 en Arduino IDE (paquete *esp32 by Espressif Systems*) o usa PlatformIO.
2. Abre `practica-03/src/practica03.ino`. Los archivos `.h` y `.cpp` deben estar en la misma carpeta.
3. Selecciona la placa ESP32 correspondiente y el puerto COM.
4. Compila y sube el programa.
5. Abre el Monitor Serie a **115200 baudios**.

El código es compatible con las versiones 2.x y 3.x del core de Arduino-ESP32 (la API de `ledc` cambió entre ambas y se resuelve con compilación condicional).

## Salida esperada en el Monitor Serie

```
=== Practica 3: Nodos IoT heterogeneos (ESP32) ===
[RED] SENS_POT conectado en pin 34
[RED] ACT_LED conectado en pin 23
[SENS_POT] ADC: 1850 (45%) | 1.49 V | Umbral: 3000
[ACT_LED] Estado: ON | PWM: 115/255
[EVENTO] SENS_POT: ALERTA activada (umbral superado)
[EVENTO] SENS_POT: lectura normalizada
```

*(Los valores numéricos dependen de la posición del potenciómetro.)*

## Parámetros configurables

| Parámetro | Dónde | Valor actual |
|-----------|-------|--------------|
| Pin del potenciómetro | `practica03.ino` (`PIN_POT`) | 34 |
| Pin del LED | `practica03.ino` (`PIN_LED`) | 23 |
| Umbral de alerta | `practica03.ino` (constructor del sensor) | 3000 |
| Periodo de parpadeo | `NodoActuadorFisico.cpp` (`PERIODO_PARPADEO`) | 100 ms |
| Frecuencia / resolución PWM | `NodoActuadorFisico.cpp` | 5000 Hz / 8 bits |
| Intervalo de reporte serie | `.cpp` del sensor y del actuador | 500 ms |

## Evidencias

- **Reporte PDF:** [`docs/Reporte_Evidencias_P3.pdf`](docs/Reporte_Evidencias_P3.pdf)
- **Video demostrativo (máx. 3 min):** (https://youtu.be/8ZlP-GZZWmY?is=7agD5jShdIdrndoA)

## Autores

Consulta el archivo [`AUTHORS`](../AUTHORS) en la raíz del repositorio.
