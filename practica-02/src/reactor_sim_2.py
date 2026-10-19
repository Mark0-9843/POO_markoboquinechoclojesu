import os
import random

historial_eventos = []


def registrar_evento(mensaje):
    """Guarda un evento y conserva solo los últimos 5."""
    historial_eventos.append(mensaje)
    if len(historial_eventos) > 5:
        historial_eventos.pop(0)


class NodoIoT:
    def __init__(self, id_dispositivo, ip, ubicacion):
        self.id_dispositivo = id_dispositivo
        self.ip = ip
        self.ubicacion = ubicacion
        self.conectado = False

    def conectar(self):
        self.conectado = True
        registrar_evento(f"[RED] {self.id_dispositivo} conectado en {self.ip}")

    def enviar_telemetria(self):
        enlace = "ONLINE" if self.conectado else "OFFLINE"
        return f"{self.id_dispositivo:<8} | {self.ip:<13} | {enlace:<7}"


class NodoSensor(NodoIoT):
    def __init__(self, id_dispositivo, ip, ubicacion, nombre, unidad, rango_min, rango_max, limite_alerta):
        super().__init__(id_dispositivo, ip, ubicacion)
        self.nombre = nombre
        self.unidad = unidad
        self.rango_min = rango_min
        self.rango_max = rango_max
        self.valor_actual = 0.0
        self.__limite_alerta = None
        self.limite_alerta = limite_alerta

    @property  # convierte el método en atributo de lectura: sensor.limite_alerta
    def limite_alerta(self):
        return self.__limite_alerta # devuelve el atributo privado

    @limite_alerta.setter    # setter: se ejecuta al asignar con =
    def limite_alerta(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise TypeError("El límite debe ser numérico.")
        if not (self.rango_min <= valor <= self.rango_max):
            raise ValueError(f"Límite fuera de rango [{self.rango_min} - {self.rango_max}].")
        self.__limite_alerta = float(valor)    # si todo es válido, guarda el dato como float en el privado

    def leer(self):
        self.valor_actual = round(random.uniform(self.rango_min, self.rango_max), 2)
        registrar_evento(f"[LECTURA] {self.nombre}: {self.valor_actual} {self.unidad}")

    def enviar_telemetria(self):
        alerta = " ⚠ ALERTA" if self.valor_actual > self.__limite_alerta else ""
        return (f"{super().enviar_telemetria()} | SENSOR   {self.nombre:<10} | "
                f"Lectura: {self.valor_actual:>7} {self.unidad}{alerta}")


class NodoActuador(NodoIoT):
    def __init__(self, id_dispositivo, ip, ubicacion, nombre):
        super().__init__(id_dispositivo, ip, ubicacion)
        self.nombre = nombre
        self.__estado_activo = False
        self.__potencia_pwm = 0.0

    @property
    def estado_activo(self):
        return self.__estado_activo

    @property
    def potencia_pwm(self):
        return self.__potencia_pwm

    def _asignar_potencia(self, valor):
        self.__potencia_pwm = valor

    def encender(self):
        self.__estado_activo = True
        registrar_evento(f"[+] {self.nombre} -> ENCENDIDO")

    def apagar(self):
        self.__estado_activo = False
        registrar_evento(f"[-] {self.nombre} -> APAGADO")

    def ajustar(self, valor):
        if 0.0 <= valor <= 100.0:
            self.__potencia_pwm = valor
            self.__estado_activo = valor > 0
            registrar_evento(f"[AJUSTE] {self.nombre} -> PWM al {valor:.1f}%")
        else:
            registrar_evento(f"[ERROR] {self.nombre} -> {valor}% fuera de rango (0-100)")

    def enviar_telemetria(self):
        estado = "ON" if self.__estado_activo else "OFF"
        return (f"{super().enviar_telemetria()} | ACTUADOR {self.nombre:<10} | "
                f"Estado: {estado:<3} | PWM: {self.__potencia_pwm:>5.1f}%")


class ActuadorDigital(NodoActuador):
    """Actuador binario (0 o 1)"""

    def encender(self):
        super().encender()
        self._asignar_potencia(1)

    def apagar(self):
        super().apagar()
        self._asignar_potencia(0)

    def ajustar(self, valor):
        if valor == 1:
            self.encender()
        elif valor == 0:
            self.apagar()
        else:
            registrar_evento(f"[ERROR] {self.nombre} es digital: solo acepta 0 o 1")

    def enviar_telemetria(self):
        estado = "ON" if self.estado_activo else "OFF"
        return (f"{NodoIoT.enviar_telemetria(self)} | DIGITAL  {self.nombre:<10} | "
                f"Estado: {estado:<3} | Valor: {int(self.potencia_pwm)}")


def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')


def mostrar_hmi(red_iot, modo="MANUAL"):
    print("=" * 100)
    print(f"  PANEL DE CONTROL HMI - MODO: [{modo}]")
    print("=" * 100)
    print(" [TELEMETRÍA DE LA RED IoT]")
    for dispositivo in red_iot:  # polimorfismo
        print(f"   ► {dispositivo.enviar_telemetria()}")
    print("=" * 100)
    print(" [REGISTRO DE EVENTOS]")
    if not historial_eventos:
        print("   (Sin actividad reciente)")
    for evento in historial_eventos:
        print(f"   {evento}")
    print("=" * 100)


def main():
    termometro = NodoSensor("SEN-001", "192.168.1.21", "Reactor", "Termometro", "°C", 0, 150, 85)
    presion = NodoSensor("SEN-002", "192.168.1.22", "Reactor", "Presion", "Bar", 0, 15, 12)
    bomba = NodoActuador("ACT-001", "192.168.1.11", "Enfriamiento", "Bomba")
    valvula = ActuadorDigital("ACT-002", "192.168.1.12", "Alivio", "Valvula")

    red_iot = [termometro, bomba, presion, valvula]

    for dispositivo in red_iot:
        dispositivo.conectar()

    bomba.ajustar(75.5)
    valvula.ajustar(1)

    # Bucle principal
    while True:
        termometro.leer()
        presion.leer()

        limpiar_pantalla()
        mostrar_hmi(red_iot)

        try:
            entrada = input("Enter para actualizar | 'terminar' para salir >> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if entrada == "terminar":
            print("\n[+] Simulación finalizada.")
            break

if __name__ == "__main__":
    main()
