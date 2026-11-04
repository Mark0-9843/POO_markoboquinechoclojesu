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
    def __init__(self, id_dispositivo, ip, ubicacion, nombre, unidad, rango_min, rango_max,
                 limite_alerta, simulacion_aleatoria=True):
        super().__init__(id_dispositivo, ip, ubicacion)
        self.nombre = nombre
        self.unidad = unidad
        self.rango_min = rango_min
        self.rango_max = rango_max
        self.valor_actual = 0.0
        self.simulacion_aleatoria = simulacion_aleatoria  # False: el valor lo mueve el modo AUTO
        self.__limite_alerta = None
        self.limite_alerta = limite_alerta

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
        if self.simulacion_aleatoria:
            self.valor_actual = round(random.uniform(self.rango_min, self.rango_max * 0.5), 2)
        registrar_evento(f"[LECTURA] {self.nombre}: {self.valor_actual} {self.unidad}")

    def excede_limite(self):
        """True si la lectura actual supera el límite de alerta."""
        return self.valor_actual > self.__limite_alerta

    def enviar_telemetria(self):
        alerta = " ⚠ ALERTA" if self.excede_limite() else ""
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
    """Actuador binario (0 o 1), ej. una válvula todo/nada."""

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


def mostrar_hmi(red_iot, modo="MANUAL", interlock_activo=False):
    print("=" * 100)
    print(f"  PANEL DE CONTROL HMI - MODO: [{modo}]")
    if interlock_activo:
        print("  🚨 INTERLOCK DE SEGURIDAD ACTIVO - CONTROL DEL OPERARIO BLOQUEADO 🚨".center(100))
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


def ejecutar_modo_automatico(actuadores, sensores, consigna_temp=50.0):
    """
    Control proporcional de la bomba para estabilizar la temperatura:
    ΔT = (+1.5°C) - (0.05°C × % de potencia de la bomba)
    """
    bomba = actuadores["bomba"]
    termometro = sensores["termometro"]

    error = termometro.valor_actual - consigna_temp
    nuevo_pwm = max(0.0, min(100.0, 30.0 + error * 2.0))  # limitado a 0-100 %
    bomba.ajustar(nuevo_pwm)

    delta_t = 1.5 - 0.05 * bomba.potencia_pwm
    termometro.valor_actual = round(termometro.valor_actual + delta_t, 2)

    registrar_evento(f"[AUTO] Bomba {bomba.potencia_pwm:.1f}% | ΔT: {delta_t:+.2f}°C | Temp: {termometro.valor_actual:.2f}°C")


def ejecutar_modo_pruebas(actuadores, sensores):
    """Inyecta un fallo aleatorio por ciclo para validar los límites y la seguridad del sistema."""
    fallo = random.choice(["sobrecalentamiento", "sobrepresion", "falla_bomba", "falla_valvula", "sin_novedad"])

    if fallo == "sobrecalentamiento":
        temp = round(random.uniform(151.0, 180.0), 2)
        sensores["termometro"].valor_actual = temp
        registrar_evento(f"[PRUEBA] Sobrecalentamiento inyectado: {temp} °C")

    elif fallo == "sobrepresion":
        pres = round(random.uniform(15.5, 25.0), 2)
        sensores["presion"].valor_actual = pres
        registrar_evento(f"[PRUEBA] Sobrepresión inyectada: {pres} Bar")

    elif fallo == "falla_bomba":
        valor = round(random.uniform(105.0, 150.0), 1)
        registrar_evento("[PRUEBA] Intentando modular la bomba fuera de rango...")
        actuadores["bomba"].ajustar(valor)

    elif fallo == "falla_valvula":
        valor = random.choice([-1, 2, 5, 9])
        registrar_evento("[PRUEBA] Enviando valor lógico inválido a la válvula...")
        actuadores["valvula"].ajustar(valor)

    else:
        registrar_evento("[PRUEBA] Monitoreo estable. Sin anomalías en este ciclo.")


def verificar_interlocks_seguridad(actuadores, sensores):
    """
    Se evalúa en cada ciclo, sin importar el modo. Si algún sensor supera su límite
    de alerta (Temp > 85 °C o Presión > 12 Bar) fuerza Bomba al 100 % y Válvula abierta.
    Devuelve True si el interlock está activo (el control del operario queda bloqueado).
    """
    if not any(sensor.excede_limite() for sensor in sensores.values()):
        return False

    bomba = actuadores["bomba"]
    valvula = actuadores["valvula"]
    if bomba.potencia_pwm != 100.0:
        bomba.ajustar(100.0)
    if valvula.potencia_pwm != 1:
        valvula.encender()

    temp = sensores["termometro"].valor_actual
    pres = sensores["presion"].valor_actual
    registrar_evento(f"[🚨 INTERLOCK] T={temp:.2f}°C, P={pres:.2f}Bar -> Bomba 100% / Válvula ABIERTA. Control bloqueado.")
    return True


def mostrar_comandos(modo, interlock_activo=False):
    print(" COMANDOS DISPONIBLES:")
    print("   • modo <manual/auto/pruebas> (Cambia el modo de operación)")
    print("   • encender <actuador>        (Ej: encender bomba)")
    print("   • apagar <actuador>          (Ej: apagar valvula)")
    print("   • ajustar <actuador> <val>   (Ej: ajustar bomba 75.5  /  ajustar valvula 1)")
    print("   • leer <sensor>              (Ej: leer termometro  /  leer presion)")
    print("   • terminar                   (Finaliza la simulación)")
    if modo == "AUTO":
        print("   ⚠ Modo AUTO: control manual bloqueado. Enter avanza un ciclo.")
    elif modo == "PRUEBAS":
        print("   ⚠ Modo PRUEBAS: cada Enter inyecta un fallo aleatorio.")
    if interlock_activo:
        print("   ⚠ Interlock activo: encender / apagar / ajustar desactivados.")
    print("=" * 100)


def procesar_comando(entrada, actuadores, sensores):
    """Interpreta el comando del operario y lo ejecuta sobre el dispositivo."""
    partes = entrada.split()
    comando = partes[0].lower()

    if comando in ("encender", "apagar", "ajustar", "leer"):
        if len(partes) < 2:
            registrar_evento(f"[ERROR] Falta el dispositivo. Uso: {comando} <nombre>")
            return
        nombre = partes[1].lower()

        if comando == "leer":
            if nombre in sensores:
                sensores[nombre].leer()
            else:
                registrar_evento(f"[ERROR] Sensor '{nombre}' no existe. Opciones: {', '.join(sensores)}")
            return

        if nombre not in actuadores:
            registrar_evento(f"[ERROR] Actuador '{nombre}' no existe. Opciones: {', '.join(actuadores)}")
            return
        actuador = actuadores[nombre]

        if comando == "encender":
            actuador.encender()
        elif comando == "apagar":
            actuador.apagar()
        else:  # ajustar
            if len(partes) < 3:
                registrar_evento("[ERROR] Falta el valor. Uso: ajustar <actuador> <valor>")
                return
            try:
                actuador.ajustar(float(partes[2]))
            except ValueError:
                registrar_evento("[ERROR] El valor de ajuste debe ser numérico.")
    else:
        registrar_evento(f"[ERROR] Comando '{comando}' no reconocido.")


def main():
    termometro = NodoSensor("SEN-001", "192.168.1.21", "Reactor", "Termometro", "°C", 0, 150, 85,
                            simulacion_aleatoria=False)
    presion = NodoSensor("SEN-002", "192.168.1.22", "Reactor", "Presion", "Bar", 0, 15, 12)
    bomba = NodoActuador("ACT-001", "192.168.1.11", "Enfriamiento", "Bomba")
    valvula = ActuadorDigital("ACT-002", "192.168.1.12", "Alivio", "Valvula")

    red_iot = [termometro, bomba, presion, valvula]

    # Diccionarios para buscar por nombre lo que escribe el operario
    actuadores = {"bomba": bomba, "valvula": valvula}
    sensores = {"termometro": termometro, "presion": presion}

    for dispositivo in red_iot:
        dispositivo.conectar()

    modo_operacion = "MANUAL"
    interlock_activo = False

    # Bucle principal: ejecuta el modo, aplica los interlocks, refresca la pantalla y atiende comandos
    while True:
        if modo_operacion == "AUTO":
            ejecutar_modo_automatico(actuadores, sensores)
        elif modo_operacion == "PRUEBAS":
            ejecutar_modo_pruebas(actuadores, sensores)

        # Los interlocks se evalúan SIEMPRE, sin importar el modo
        interlock_activo = verificar_interlocks_seguridad(actuadores, sensores)

        limpiar_pantalla()
        mostrar_hmi(red_iot, modo_operacion, interlock_activo)
        mostrar_comandos(modo_operacion, interlock_activo)

        try:
            entrada = input("Ingrese comando >> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not entrada:
            continue  # en AUTO y PRUEBAS, Enter avanza un ciclo
        if entrada.lower() == "terminar":
            print("\n[+] Simulación finalizada.")
            break

        partes = entrada.split()
        comando = partes[0].lower()

        if comando == "modo":
            if len(partes) > 1 and partes[1].upper() in ("MANUAL", "AUTO", "PRUEBAS"):
                modo_operacion = partes[1].upper()
                registrar_evento(f"[SISTEMA] Modo de operación cambiado a: {modo_operacion}")
            else:
                registrar_evento("[ERROR] Uso: modo <manual/auto/pruebas>")
        elif comando in ("encender", "apagar", "ajustar") and interlock_activo:
            registrar_evento("[DENEGADO] Interlock de seguridad activo. Control del operario bloqueado.")
        elif modo_operacion == "AUTO":
            registrar_evento("[DENEGADO] Control manual bloqueado durante el modo AUTO.")
        else:
            procesar_comando(entrada, actuadores, sensores)


if __name__ == "__main__":
    main()

