import os
import random

historial_eventos = []

def registrar_evento(mensaje: str):
    """Agrega un evento al historial y mantiene solo los últimos 5."""
    historial_eventos.append(mensaje)
    if len(historial_eventos) > 5:
        historial_eventos.pop(0)

def limpiar_pantalla():
    """Limpia la terminal según el sistema operativo."""
    os.system('cls' if os.name == 'nt' else 'clear')


class Actuador:
    """Clase base para todos los actuadores."""
    def __init__(self, nombre: str):
        self.nombre = nombre
        self.estado = False # Inicializa el actuador apagado por defecto

    def encender(self):
        self.estado = True # Cambia el estado interno a encendido
        registrar_evento(f"[+] {self.nombre} -> Estado cambiado a: ENCENDIDO (ON)")

    def apagar(self):
        self.estado = False # Cambia el estado interno a apagado
        registrar_evento(f"[-] {self.nombre} -> Estado cambiado a: APAGADO (OFF)")


class ActuadorProporcional(Actuador):
    """Actuador que opera en un rango analógico de 0% a 100%."""
    def __init__(self, nombre: str):
        super().__init__(nombre) # Llama al constructor de la clase base
        # Define los límites y el valor actual (inicia en 0)
        self.rango_operacion_min = 0.0
        self.rango_operacion_max = 100.0
        self.punto_operacion = 0.0

    def ajustar(self, valor: float):
        # Valida que el valor esté dentro del rango permitido (0 - 100)
        if self.rango_operacion_min <= valor <= self.rango_operacion_max:
            self.punto_operacion = valor
            # Se considera "encendido" si el valor es mayor a 0
            if valor > 0:
                self.estado = True
            else:
                self.estado = False
            registrar_evento(f"[⚙] {self.nombre} -> Punto de operación ajustado al {self.punto_operacion:.1f}%")
        else:
            # Manejo de error si el valor está fuera de límite
            registrar_evento(f"[⚠️ ERROR] {self.nombre} -> Valor {valor}% fuera de rango (0% - 100%).")

    def info(self) -> str:
        # Retorna una cadena con los datos del actuador tabulados
        estado_str = "ON" if self.estado else "OFF"
        return f"{self.nombre:<20} | Estado: {estado_str:<3} | Punto Op: {self.punto_operacion:>5.1f}% | Rango: [0.0% - 100.0%]"


class ActuadorDigital(Actuador):
    """Actuador que opera de manera binaria (0 o 1)."""
    def __init__(self, nombre: str):
        super().__init__(nombre)
        self.punto_operacion = 0 # Inicia en 0 (apagado)

    def encender(self):
        super().encender() # Usa la lógica de la clase base
        self.punto_operacion = 1 # Actualiza su valor numérico

    def apagar(self):
        super().apagar() # Usa la lógica de la clase base
        self.punto_operacion = 0 # Actualiza su valor numérico

    def ajustar(self, valor: float):
        # Restringe la entrada estrictamente a valores booleanos (1 o 0)
        if valor == 1:
            self.encender()
        elif valor == 0:
            self.apagar()
        else:
            registrar_evento(f"[⚠️ ERROR] {self.nombre} -> Es digital. Solo acepta valores de 0 o 1.")

    def info(self) -> str:
        # Retorna los datos formateados específicos para actuadores digitales
        estado_str = "ON" if self.estado else "OFF"
        return f"{self.nombre:<20} | Estado: {estado_str:<3} | Valor:    {self.punto_operacion:>3} | Rango: [0 / 1 (Digital)]"


class Sensor:
    """Clase para simular el comportamiento de un sensor."""
    def __init__(self, nombre: str, variable_fisica: str, rango_min: float, rango_max: float, sensibilidad: float, decimales_medicion: int, unidad: str):
        # Asigna los parámetros iniciales del sensor
        self.nombre = nombre
        self.variable_fisica = variable_fisica
        self.rango_min = rango_min
        self.rango_max = rango_max
        self.sensibilidad = sensibilidad
        self.decimales_medicion = decimales_medicion
        self.unidad = unidad
        # Calcula un valor inicial aleatorio dentro del primer tercio del rango
        self.valor_actual = round((rango_min + rango_max) / 3.0, decimales_medicion)

    def leer_valor_actual(self) -> float:
        # Simula una lectura aleatoria para sensores que NO sean de temperatura
        if self.variable_fisica != "Temperatura":
            self.valor_actual = round(random.uniform(self.rango_min, self.rango_max * 0.5), self.decimales_medicion)

        # Formatea el valor y registra el evento de lectura
        lectura_str = f"{self.valor_actual:.{self.decimales_medicion}f} {self.unidad}"
        registrar_evento(f"[📊 LECTURA] {self.nombre}: {lectura_str} (Var: {self.variable_fisica})")
        return self.valor_actual

    def info(self) -> str:
        # Retorna una cadena con la información detallada del sensor formateada
        return f"{self.nombre:<20} | Var: {self.variable_fisica:<18} | Rango: [{self.rango_min:>4.1f} - {self.rango_max:>5.1f}] {self.unidad:<5} | Sensibilidad: {self.sensibilidad} | Dec: {self.decimales_medicion}"

def ejecutar_modo_automatico(actuadores, sensores, consigna_temp=50.0):
    """
    Algoritmo de estabilidad dinámica:
    ΔT = (+1.5°C) - (0.05°C × % OperaciónBomba)
    """
    bomba = actuadores["bomba"]
    sensor_temp = sensores["termometro"]

    error = sensor_temp.valor_actual - consigna_temp
    nuevo_porcentaje = 30.0 + (error * 2.0)
    nuevo_porcentaje = max(0.0, min(100.0, nuevo_porcentaje))

    bomba.ajustar(nuevo_porcentaje)

    delta_t = 1.5 - (0.05 * bomba.punto_operacion)
    sensor_temp.valor_actual = round(sensor_temp.valor_actual + delta_t, sensor_temp.decimales_medicion)

    registrar_evento(f"[🤖 AUTO] Bomba al {bomba.punto_operacion:.1f}% | ΔT: {delta_t:+.2f}°C | Temp: {sensor_temp.valor_actual:.2f}°C")


def ejecutar_modo_pruebas(actuadores, sensores):
    """
    Rutina que inyecta fallos aleatorios en el sistema para validar
    límites operativos y mecanismos de seguridad del HMI.
    """
    fallos_posibles = ["sobrecalentamiento", "sobrepresion", "falla_bomba", "falla_valvula", "sin_novedad"]
    fallo = random.choice(fallos_posibles)

    if fallo == "sobrecalentamiento":
        temp_critica = round(random.uniform(151.0, 180.0), sensores["termometro"].decimales_medicion)
        sensores["termometro"].valor_actual = temp_critica
        registrar_evento(f"[🔥 ALERTA PRUEBA] Límite térmico excedido. Temp inyectada: {temp_critica} °C")

    elif fallo == "sobrepresion":
        pres_critica = round(random.uniform(15.5, 25.0), sensores["presion"].decimales_medicion)
        sensores["presion"].valor_actual = pres_critica
        registrar_evento(f"[💥 ALERTA PRUEBA] Límite barométrico excedido. Presión inyectada: {pres_critica} Bar")

    elif fallo == "falla_bomba":
        falla_porcentaje = round(random.uniform(105.0, 150.0), 1)
        registrar_evento("[⚙️ PRUEBA] Inyectando fallo: Intentando modular bomba fuera de límite...")
        actuadores["bomba"].ajustar(falla_porcentaje)

    elif fallo == "falla_valvula":
        falla_logica = random.choice([-1, 2, 5, 9])
        registrar_evento("[🚰 PRUEBA] Inyectando fallo: Valor lógico no reconocido en válvula...")
        actuadores["valvula"].ajustar(falla_logica)

    elif fallo == "sin_novedad":
        registrar_evento("[🧪 PRUEBA] Monitoreo estable. Sin anomalías inyectadas en este ciclo.")


def verificar_interlocks_seguridad(actuadores, sensores) -> bool:
    """
    Se evalúa en cada ciclo, sin importar el modo de operación activo.
    Si Temperatura > 85.0 °C o Presión > 12.0 Bar, el sistema ignora
    cualquier instrucción del operario y fuerza simultáneamente:
      - Bomba de Enfriamiento al 100%
      - Válvula de Alivio totalmente abierta
    Devuelve True mientras la condición crítica siga activa (y por lo
    tanto el control manual/automático debe permanecer bloqueado).
    """
    temp = sensores["termometro"].valor_actual
    pres = sensores["presion"].valor_actual

    if temp > 85.0 or pres > 12.0:
        bomba = actuadores["bomba"]
        valvula = actuadores["valvula"]

        if bomba.punto_operacion != 100.0:
            bomba.ajustar(100.0)
        if valvula.punto_operacion != 1:
            valvula.encender()

        registrar_evento(
            f"[🚨 INTERLOCK] Condición crítica (T={temp:.2f}°C, P={pres:.2f}Bar) -> "
            f"Bomba forzada 100% / Válvula ABIERTA. Control del operario BLOQUEADO."
        )
        return True

    return False


def mostrar_interfaz_hmi(actuadores, sensores, modo_operacion, interlock_activo=False):
    print("=" * 95)
    print(f"            PANEL DE CONTROL INDUSTRIAL HMI - MODO: [{modo_operacion.upper()}]")
    if interlock_activo:
        print(" 🚨 INTERLOCK DE SEGURIDAD ACTIVO - CONTROL DEL OPERARIO BLOQUEADO 🚨".center(95))
    print("=" * 95)

    print(" [ACTUADORES]")
    for key, act in actuadores.items():
        print(f"   ► [{key:<7}] {act.info()}")
    print("-" * 95)

    print(" [SENSORES]")
    for key, sen in sensores.items():
        print(f"   ► [{key:<10}] {sen.info()} | Lectura: {sen.valor_actual} {sen.unidad}")
    print("=" * 95)

    print(" [REGISTRO DE EVENTOS EN VIVO (SCADA/HMI)]")
    if not historial_eventos:
        print("   (Sin actividad reciente)")
    else:
        for ev in historial_eventos:
            print(f"   {ev}")
    print("=" * 95)

    print(" COMANDOS DISPONIBLES:")
    print("   • modo <manual/auto/pruebas> (Cambia el modo de operación)")
    print("   • encender <actuador>        (Ej: encender bomba)")
    print("   • apagar <actuador>          (Ej: apagar valvula)")
    print("   • ajustar <actuador> <val>   (Ej: ajustar bomba 75.5  O  ajustar valvula 1)")
    print("   • leer <sensor>              (Ej: leer termometro     O  leer presion)")
    print("   • terminar                   (Finaliza la simulación)")
    if interlock_activo:
        print("   ⚠ Interlock de seguridad activo: comandos de control desactivados.")
    print("=" * 95)


def main():
    Bomba_de_Enfriamiento = ActuadorProporcional("Bomba de Enfriamiento")
    Valvula_de_Alivio = ActuadorDigital("Válvula de Alivio")

    termometro = Sensor("Termometro", "Temperatura", 0.0, 150.0, 0.01, 3, "°C")
    termometro.valor_actual = 0
    presion = Sensor("Presion", "Presion", 0.0, 15.0, 0.001, 2, "Bar")

    actuadores = {"bomba": Bomba_de_Enfriamiento, "valvula": Valvula_de_Alivio}
    sensores = {"termometro": termometro, "presion": presion}

    modo_operacion = "MANUAL"
    interlock_activo = False

    while True:
        if modo_operacion == "AUTO":
            ejecutar_modo_automatico(actuadores, sensores)
        elif modo_operacion == "PRUEBAS":
            ejecutar_modo_pruebas(actuadores, sensores)

        interlock_activo = verificar_interlocks_seguridad(actuadores, sensores)

        limpiar_pantalla()
        mostrar_interfaz_hmi(actuadores, sensores, modo_operacion, interlock_activo)

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

        if comando == "modo":
            if len(partes) < 2:
                registrar_evento("[⚠️ ERROR] Uso: modo <manual/auto/pruebas>")
                continue
            nuevo_modo = partes[1].upper()
            if nuevo_modo in ["MANUAL", "AUTO", "PRUEBAS"]:
                modo_operacion = nuevo_modo
                registrar_evento(f"[🔄 SISTEMA] Modo de operación cambiado a: {modo_operacion}")
            else:
                registrar_evento("[⚠️ ERROR] Modo no válido. Opciones: manual, auto, pruebas")

        elif comando == "encender":
            if interlock_activo:
                registrar_evento("[⚠️ DENEGADO] Interlock de seguridad activo. Control manual bloqueado.")
                continue
            if modo_operacion == "AUTO":
                registrar_evento("[⚠️ DENEGADO] Control manual bloqueado durante Modo Automático.")
                continue
            if len(partes) < 2:
                registrar_evento("[⚠️ ERROR] Especifica el actuador. Uso: encender <bomba/valvula>")
                continue
            target = partes[1].lower()
            if target in actuadores:
                actuadores[target].encender()
            else:
                registrar_evento(f"[⚠️ ERROR] Actuador '{target}' no existe. Opciones: bomba, valvula")

        elif comando == "apagar":
            if interlock_activo:
                registrar_evento("[⚠️ DENEGADO] Interlock de seguridad activo. Control manual bloqueado.")
                continue
            if modo_operacion == "AUTO":
                registrar_evento("[⚠️ DENEGADO] Control manual bloqueado durante Modo Automático.")
                continue
            if len(partes) < 2:
                registrar_evento("[⚠️ ERROR] Especifica el actuador. Uso: apagar <bomba/valvula>")
                continue
            target = partes[1].lower()
            if target in actuadores:
                actuadores[target].apagar()
            else:
                registrar_evento(f"[⚠️ ERROR] Actuador '{target}' no existe. Opciones: bomba, valvula")

        elif comando == "ajustar":
            if interlock_activo:
                registrar_evento("[⚠️ DENEGADO] Interlock de seguridad activo. Control manual bloqueado.")
                continue
            if modo_operacion == "AUTO":
                registrar_evento("[⚠️ DENEGADO] Control manual bloqueado durante Modo Automático.")
                continue
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
