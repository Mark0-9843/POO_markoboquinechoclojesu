import random

class NodoIoT:
    """Superclase: atributos y métodos comunes de todo dispositivo."""

    def __init__(self, id_dispositivo, ip, ubicacion):
        self.id_dispositivo = id_dispositivo
        self.ip = ip
        self.ubicacion = ubicacion
        self.conectado = False

    def conectar(self):
        self.conectado = True
        print(f"[RED] {self.id_dispositivo} conectado en {self.ip}")

    def enviar_telemetria(self):
        print(f"[{self.id_dispositivo}] {self.ubicacion} | conectado: {self.conectado}")


class NodoSensor(NodoIoT):
    def __init__(self, id_dispositivo, ip, ubicacion, unidad, rango_min, rango_max, limite_alerta):
        super().__init__(id_dispositivo, ip, ubicacion)
        self.unidad = unidad
        self.rango_min = rango_min
        self.rango_max = rango_max
        self.valor_actual = 0.0
        self.__limite_alerta = None
        self.limite_alerta = limite_alerta  # pasa por el setter

    @property
    def limite_alerta(self):
        return self.__limite_alerta

    @limite_alerta.setter
    def limite_alerta(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise TypeError("El límite debe ser numérico.")
        if not (self.rango_min <= valor <= self.rango_max):
            raise ValueError(f"Límite fuera de rango [{self.rango_min} - {self.rango_max}].")
        self.__limite_alerta = float(valor)

    def leer(self):
        self.valor_actual = round(random.uniform(self.rango_min, self.rango_max), 2)

    def enviar_telemetria(self):
        self.leer()
        alerta = " ⚠ ALERTA" if self.valor_actual > self.__limite_alerta else ""
        print(f"[{self.id_dispositivo}] Lectura: {self.valor_actual} {self.unidad}{alerta}")


class NodoActuador(NodoIoT):
    def __init__(self, id_dispositivo, ip, ubicacion):
        super().__init__(id_dispositivo, ip, ubicacion)
        self.__estado_activo = False
        self.__potencia_pwm = 0.0

    def encender(self):
        self.__estado_activo = True
        self.__potencia_pwm = 100.0

    def apagar(self):
        self.__estado_activo = False
        self.__potencia_pwm = 0.0

    def enviar_telemetria(self):
        estado = "ON" if self.__estado_activo else "OFF"
        print(f"[{self.id_dispositivo}] Estado: {estado} | PWM: {self.__potencia_pwm}%")


def main():
    sensor_temp = NodoSensor("SEN-001", "192.168.1.21", "Reactor", "°C", 0, 150, 85)
    sensor_luz = NodoSensor("SEN-002", "192.168.1.22", "Sala", "lux", 0, 1000, 800)
    ventilador = NodoActuador("ACT-001", "192.168.1.11", "Enfriamiento")

    red_iot = [sensor_temp, ventilador, sensor_luz]

    for dispositivo in red_iot:
        dispositivo.conectar()

    ventilador.encender()

    # Bucle polimórfico: cada objeto responde según su clase
    for dispositivo in red_iot:
        dispositivo.enviar_telemetria()


if __name__ == "__main__":
    main()

