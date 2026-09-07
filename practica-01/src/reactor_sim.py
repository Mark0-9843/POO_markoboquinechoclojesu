"""
EE: Programación Orientada a Objetos (UV)
Ejemplo Integrador v7: Panel HMI Estático con Limpieza de Pantalla y Registro de Eventos
Este script simula un panel de control industrial estático (no scroll) mediante borrado de pantalla.

Versión 1.0.0, ejemplo dado en clase.
"""

import os
import random

# Lista global para simular un registrador de eventos (Event Logger) tipo SCADA/HMI
# Esto evita que los mensajes de acción se borren al limpiar la pantalla
historial_eventos = []

def registrar_evento(mensaje: str):
    """Agrega un evento al historial y mantiene solo los últimos 5 para que no desplace la pantalla."""
    historial_eventos.append(mensaje)
    if len(historial_eventos) > 5:
        historial_eventos.pop(0)

def limpiar_pantalla():
    """Limpia la terminal según el sistema operativo (cls para Windows, clear para Unix)."""
    os.system('cls' if os.name == 'nt' else 'clear')


# ==============================================================================
# 1. CLASE ACTUADOR
# ==============================================================================
class Actuador:
    def __init__(self, nombre: str):
        # Atributos de estado del actuador
        self.nombre = nombre
        self.rango_operacion_min = 0.0   # Límite mínimo de operación (0%)
        self.rango_operacion_max = 100.0 # Límite máximo de operación (100%)
        self.estado = False              # Estado lógico de encendido: False = OFF, True = ON
        self.punto_operacion = 0.0       # Porcentaje actual de operación

    def encender(self):
        """Cambia el estado lógico a ON y registra la acción."""
        self.estado = True
        registrar_evento(f"[+] {self.nombre} -> Estado cambiado a: ENCENDIDO (ON)")

    def apagar(self):
        """Cambia el estado lógico a OFF y registra la acción."""
        self.estado = False
        registrar_evento(f"[-] {self.nombre} -> Estado cambiado a: APAGADO (OFF)")

    def ajustar(self, valor: float):
        """Ajusta el punto de operación si está dentro del rango permitido."""
        if self.rango_operacion_min <= valor <= self.rango_operacion_max:
            self.punto_operacion = valor
            registrar_evento(f"[⚙] {self.nombre} -> Punto de operación ajustado al {self.punto_operacion:.1f}%")
        else:
            registrar_evento(f"[⚠️ ERROR] {self.nombre} -> Valor {valor}% fuera de rango (0% - 100%).")

    def info(self) -> str:
        """Retorna una cadena con el estado formateado del actuador."""
        estado_str = "ON" if self.estado else "OFF"
        return f"{self.nombre:<20} | Estado: {estado_str:<3} | Punto Op: {self.punto_operacion:>5.1f}% | Rango: [0.0% - 100.0%]"


# ==============================================================================
# 2. CLASE SENSOR
# ==============================================================================
class Sensor:
    def __init__(self, nombre: str, variable_fisica: str, rango_min: float, rango_max: float, sensibilidad: float, decimales_medicion: int, unidad: str):
        # Atributos de especificación técnica del sensor
        self.nombre = nombre
        self.variable_fisica = variable_fisica
        self.rango_min = rango_min
        self.rango_max = rango_max
        self.sensibilidad = sensibilidad
        self.decimales_medicion = decimales_medicion
        self.unidad = unidad

    def leer_valor_actual(self) -> float:
        """Simula una lectura física, la redondea a la precisión dada y la registra en eventos."""
        valor_simulado = random.uniform(self.rango_min, self.rango_max)
        valor_redondeado = round(valor_simulado, self.decimales_medicion)
        
        # Formateamos la lectura con sus decimales y unidad correspondiente
        lectura_str = f"{valor_redondeado:.{self.decimales_medicion}f} {self.unidad}"
        registrar_evento(f"[📊 LECTURA] {self.nombre}: {lectura_str} (Var: {self.variable_fisica})")
        return valor_redondeado

    def info(self) -> str:
        """Retorna una cadena con las especificaciones técnicas del sensor."""
        return f"{self.nombre:<20} | Var: {self.variable_fisica:<18} | Rango: [{self.rango_min:>4.1f} - {self.rango_max:>5.1f}] {self.unidad:<5} | Sensibilidad: {self.sensibilidad} | Dec: {self.decimales_medicion}"


# ==============================================================================
# INTERFAZ HMI (TABLERO DE CONTROL)
# ==============================================================================
def mostrar_interfaz_hmi(actuadores, sensores):
    """Pinta el menú y los estados actuales de los objetos en una pantalla fija."""
    print("=" * 85)
    print("                PANEL DE CONTROL INDUSTRIAL HMI (ESTÁTICO)")
    print("=" * 85)
    
    # 1. Sección de Actuadores
    print(" [ACTUADORES]")
    for key, act in actuadores.items():
        print(f"   ► [{key:<7}] {act.info()}")
    print("-" * 85)
    
    # 2. Sección de Sensores
    print(" [SENSORES]")
    for key, sen in sensores.items():
        print(f"   ► [{key:<9}] {sen.info()}")
    print("=" * 85)
    
    # 3. Sección de Registro de Eventos (Event Logger)
    print(" [REGISTRO DE EVENTOS EN VIVO (SCADA/HMI)]")
    if not historial_eventos:
        print("   (Sin actividad reciente)")
    else:
        for ev in historial_eventos:
            print(f"   {ev}")
    print("=" * 85)
    
    # 4. Sección de Comandos
    print(" COMANDOS DISPONIBLES:")
    print("   • encender <actuador>       (Ej: encender bomba)")
    print("   • apagar <actuador>         (Ej: apagar valvula)")
    print("   • ajustar <actuador> <val>  (Ej: ajustar bomba 75.5)")
    print("   • leer <sensor>             (Ej: leer caudal  O  leer manometro)")
    print("   • terminar                  (Finaliza la simulación)")
    print("=" * 85)


# ==============================================================================
# BUCLE INTERACTIVO PRINCIPAL
# ==============================================================================
def main():
    # 3. Creación de dos objetos de la clase Actuador
    calefactor = Actuador("Calefactor")
    enfriador = Actuador("Enfriador")

    # 3. Creación de dos objetos de la clase Sensor
    termometro = Sensor(
        nombre="termometro",
        variable_fisica="Temperatura",
        rango_min=0.0,
        rango_max=100.0,
        sensibilidad=0.01,
        decimales_medicion=3,
        unidad="°C"
    )

    fotocelda = Sensor(
        nombre="fotocelda",
        variable_fisica="Luminosidad",
        rango_min=0.0,
        rango_max=100.0,
        sensibilidad=0.001,
        decimales_medicion=2,
        unidad="Lumenes"
    )

    # Diccionarios de mapeo para enlazar los comandos de texto con las instancias reales
    actuadores = {"calefactor": calefactor, "enfriador": enfriador}
    sensores = {"termometro": termometro, "fotocelda": fotocelda}

    # Bucle interactivo directo
    while True:
        # 1. Limpiamos la pantalla antes de volver a dibujar
        limpiar_pantalla()
        
        # 2. Dibujamos el HMI con los estados actualizados en memoria
        mostrar_interfaz_hmi(actuadores, sensores)
        
        try:
            # Solicitamos el comando de entrada al usuario
            entrada = input("Ingrese comando >> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n[+] Programa terminado.")
            break

        if not entrada:
            continue

        if entrada.lower() == "terminar":
            print("\n[+] Cerrando sistema de control... Programa finalizado con éxito.")
            break

        partes = entrada.split()
        if len(partes) == 0:
            continue

        comando = partes[0].lower()

        # Procesamiento del Comando: ENCENDER
        if comando == "encender":
            if len(partes) < 2:
                registrar_evento("[⚠️ ERROR] Especifica el actuador. Uso: encender <bomba/valvula>")
                continue
            target = partes[1].lower()
            if target in actuadores:
                actuadores[target].encender()
            else:
                registrar_evento(f"[⚠️ ERROR] Actuador '{target}' no existe. Opciones: bomba, valvula")

        # Procesamiento del Comando: APAGAR
        elif comando == "apagar":
            if len(partes) < 2:
                registrar_evento("[⚠️ ERROR] Especifica el actuador. Uso: apagar <bomba/valvula>")
                continue
            target = partes[1].lower()
            if target in actuadores:
                actuadores[target].apagar()
            else:
                registrar_evento(f"[⚠️ ERROR] Actuador '{target}' no existe. Opciones: bomba, valvula")

        # Procesamiento del Comando: AJUSTAR
        elif comando == "ajustar":
            if len(partes) < 3:
                registrar_evento("[⚠️ ERROR] Faltan parámetros. Uso: ajustar <bomba/valvula> <valor>")
                continue
            target = partes[1].lower()
            try:
                valor = float(partes[2])
                if target in actuadores:
                    actuadores[target].ajustar(valor)
                else:
                    registrar_evento(f"[⚠️ ERROR] Actuador '{target}' no existe. Opciones: bomba, valvula")
            except ValueError:
                registrar_evento("[⚠️ ERROR] El valor de ajuste debe ser numérico.")

        # Procesamiento del Comando: LEER
        elif comando == "leer":
            if len(partes) < 2:
                registrar_evento("[⚠️ ERROR] Especifica el sensor. Uso: leer <caudal/manometro>")
                continue
            target = partes[1].lower()
            if target in sensores:
                sensores[target].leer_valor_actual()
            else:
                registrar_evento(f"[⚠️ ERROR] Sensor '{target}' no existe. Opciones: caudal, manometro")

        # Comando no reconocido
        else:
            registrar_evento(f"[⚠️ ERROR] Comando '{comando}' no reconocido.")


if __name__ == "__main__":
    main()
