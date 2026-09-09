import os
import random

# Lista global para simular un registrador de eventos (Event Logger) tipo SCADA/HMI
historial_eventos = []

def registrar_evento(mensaje: str):
    """Agrega un evento al historial y mantiene solo los últimos 5."""
    historial_eventos.append(mensaje)
    if len(historial_eventos) > 5:
        historial_eventos.pop(0)

def limpiar_pantalla():
    """Limpia la terminal según el sistema operativo."""
    os.system('cls' if os.name == 'nt' else 'clear')


# ==============================================================================
# CLASES DE ACTUADORES (Implementación de Herencia)
# ==============================================================================
class Actuador:
    """Clase base para todos los actuadores."""
    def __init__(self, nombre: str):
        self.nombre = nombre
        self.estado = False              # Estado lógico de encendido: False = OFF, True = ON

    def encender(self):
        self.estado = True
        registrar_evento(f"[+] {self.nombre} -> Estado cambiado a: ENCENDIDO (ON)")

    def apagar(self):
        self.estado = False
        registrar_evento(f"[-] {self.nombre} -> Estado cambiado a: APAGADO (OFF)")

class ActuadorProporcional(Actuador):
    """Actuador que opera en un rango analógico de 0% a 100%."""
    def __init__(self, nombre: str):
        super().__init__(nombre)
        self.rango_operacion_min = 0.0   
        self.rango_operacion_max = 100.0 
        self.punto_operacion = 0.0       

    def ajustar(self, valor: float):
        if self.rango_operacion_min <= valor <= self.rango_operacion_max:
            self.punto_operacion = valor
            registrar_evento(f"[⚙] {self.nombre} -> Punto de operación ajustado al {self.punto_operacion:.1f}%")
        else:
            registrar_evento(f"[⚠️ ERROR] {self.nombre} -> Valor {valor}% fuera de rango (0% - 100%).")

    def info(self) -> str:
        estado_str = "ON" if self.estado else "OFF"
        return f"{self.nombre:<20} | Estado: {estado_str:<3} | Punto Op: {self.punto_operacion:>5.1f}% | Rango: [0.0% - 100.0%]"

class ActuadorDigital(Actuador):
    """Actuador que opera de manera binaria (0 o 1)."""
    def __init__(self, nombre: str):
        super().__init__(nombre)
        self.punto_operacion = 0

    def encender(self):
        super().encender()
        self.punto_operacion = 1

    def apagar(self):
        super().apagar()
        self.punto_operacion = 0

    def ajustar(self, valor: float):
        if valor == 1:
            self.encender()
        elif valor == 0:
            self.apagar()
        else:
            registrar_evento(f"[⚠️ ERROR] {self.nombre} -> Es digital. Solo acepta valores de 0 o 1.")

    def info(self) -> str:
        estado_str = "ON" if self.estado else "OFF"
        return f"{self.nombre:<20} | Estado: {estado_str:<3} | Valor:    {self.punto_operacion:>3} | Rango: [0 / 1 (Digital)]"


# ==============================================================================
# CLASE SENSOR
# ==============================================================================
class Sensor:
    def __init__(self, nombre: str, variable_fisica: str, rango_min: float, rango_max: float, sensibilidad: float, decimales_medicion: int, unidad: str):
        self.nombre = nombre
        self.variable_fisica = variable_fisica
        self.rango_min = rango_min
        self.rango_max = rango_max
        self.sensibilidad = sensibilidad
        self.decimales_medicion = decimales_medicion
        self.unidad = unidad

    def leer_valor_actual(self) -> float:
        valor_simulado = random.uniform(self.rango_min, self.rango_max)
        valor_redondeado = round(valor_simulado, self.decimales_medicion)
        
        lectura_str = f"{valor_redondeado:.{self.decimales_medicion}f} {self.unidad}"
        registrar_evento(f"[📊 LECTURA] {self.nombre}: {lectura_str} (Var: {self.variable_fisica})")
        return valor_redondeado

    def info(self) -> str:
        return f"{self.nombre:<20} | Var: {self.variable_fisica:<18} | Rango: [{self.rango_min:>4.1f} - {self.rango_max:>5.1f}] {self.unidad:<5} | Sensibilidad: {self.sensibilidad} | Dec: {self.decimales_medicion}"


# ==============================================================================
# INTERFAZ HMI (TABLERO DE CONTROL)
# ==============================================================================
def mostrar_interfaz_hmi(actuadores, sensores):
    # Encabezado principal del panel de control
    print("=" * 90)
    print("                           PANEL DE CONTROL INDUSTRIAL HMI (ESTÁTICO)")
    print("=" * 90)
    
    # Sección de actuadores: recorre el diccionario y muestra la info de cada uno
    print(" [ACTUADORES]")
    for key, act in actuadores.items():
        # key = nombre/identificador del actuador, act = objeto actuador con método info()
        print(f"   ► [{key:<7}] {act.info()}")
    print("-" * 90)
    
    # Sección de sensores: recorre el diccionario y muestra la info de cada uno
    print(" [SENSORES]")
    for key, sen in sensores.items():
        # key = nombre/identificador del sensor, sen = objeto sensor con método info()
        print(f"   ► [{key:<10}] {sen.info()}")
    print("=" * 90)
    
    # Sección de registro de eventos (log tipo SCADA/HMI)
    print(" [REGISTRO DE EVENTOS EN VIVO (SCADA/HMI)]")
    if not historial_eventos:
        # Si la lista de eventos está vacía, se informa que no hay actividad
        print("   (Sin actividad reciente)")
    else:
        # Si hay eventos registrados, se imprimen uno por uno
        for ev in historial_eventos:
            print(f"   {ev}")
    print("=" * 90)
    
    # Sección de ayuda: lista de comandos que el usuario puede ejecutar
    print(" COMANDOS DISPONIBLES:")
    print("   • encender <actuador>       (Ej: encender bomba)")
    print("   • apagar <actuador>         (Ej: apagar valvula)")
    print("   • ajustar <actuador> <val>  (Ej: ajustar bomba 75.5  O  ajustar valvula 1)")
    print("   • leer <sensor>             (Ej: leer termometro     O  leer presion)")
    print("   • terminar                  (Finaliza la simulación)")
    print("=" * 90)


# ==============================================================================
# BUCLE INTERACTIVO PRINCIPAL
# ==============================================================================
def main():
    # Instanciación aplicando Polimorfismo
    Bomba_de_Enfriamiento = ActuadorProporcional("Bomba de Enfriamiento")
    Valvula_de_Alivio = ActuadorDigital("Válvula de Alivio")

    termometro = Sensor("Termometro", "Temperatura", 0.0, 150.0, 0.01, 3, "°C")
    presion = Sensor("Presion", "Presion", 0.0, 15.0, 0.001, 2, "Bar")

    # Corrección de mapeo para coincidir con el uso real en terminal
    actuadores = {"bomba": Bomba_de_Enfriamiento, "valvula": Valvula_de_Alivio}
    sensores = {"termometro": termometro, "presion": presion}

    while True:
        limpiar_pantalla()
        mostrar_interfaz_hmi(actuadores, sensores)
        
        try:
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

        if comando == "encender":
            if len(partes) < 2:
                registrar_evento("[⚠️ ERROR] Especifica el actuador. Uso: encender <bomba/valvula>")
                continue
            target = partes[1].lower()
            if target in actuadores:
                actuadores[target].encender()
            else:
                registrar_evento(f"[⚠️ ERROR] Actuador '{target}' no existe. Opciones: bomba, valvula")

        elif comando == "apagar":
            if len(partes) < 2:
                registrar_evento("[⚠️ ERROR] Especifica el actuador. Uso: apagar <bomba/valvula>")
                continue
            target = partes[1].lower()
            if target in actuadores:
                actuadores[target].apagar()
            else:
                registrar_evento(f"[⚠️ ERROR] Actuador '{target}' no existe. Opciones: bomba, valvula")

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

        elif comando == "leer":
            if len(partes) < 2:
                registrar_evento("[⚠️ ERROR] Especifica el sensor. Uso: leer <termometro/presion>")
                continue
            target = partes[1].lower()
            if target in sensores:
                sensores[target].leer_valor_actual()
            else:
                registrar_evento(f"[⚠️ ERROR] Sensor '{target}' no existe. Opciones: termometro, presion")

        else:
            registrar_evento(f"[⚠️ ERROR] Comando '{comando}' no reconocido.")

if __name__ == "__main__":
    main()
