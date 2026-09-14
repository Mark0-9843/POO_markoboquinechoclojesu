import os
import random

# ==============================================================================
# ESTRUCTURAS Y FUNCIONES AUXILIARES GLOBALES
# ==============================================================================

# Lista global para simular un registrador de eventos (Event Logger) tipo SCADA/HMI
# Aquí se van acumulando los mensajes que se muestran en el panel de "Registro de eventos"
historial_eventos = []

def registrar_evento(mensaje: str):
    """Agrega un evento al historial y mantiene solo los últimos 5."""
    # Se añade el nuevo mensaje al final de la lista
    historial_eventos.append(mensaje)
    # Si ya hay más de 5 eventos guardados, se elimina el más antiguo (índice 0)
    # Esto simula un buffer circular de tamaño fijo (últimos 5 eventos visibles)
    if len(historial_eventos) > 5:
        historial_eventos.pop(0)

def limpiar_pantalla():
    """Limpia la terminal según el sistema operativo."""
    # 'cls' es el comando de limpieza en Windows (os.name == 'nt'),
    # 'clear' es el comando equivalente en sistemas tipo Unix/Linux/Mac
    os.system('cls' if os.name == 'nt' else 'clear')


# ==============================================================================
# CLASES DE ACTUADORES (Implementación de Herencia)
# ==============================================================================
class Actuador:
    """Clase base para todos los actuadores."""
    def __init__(self, nombre: str):
        self.nombre = nombre
        # Estado booleano general: True = encendido, False = apagado
        self.estado = False

    def encender(self):
        # Comportamiento genérico: solo cambia el estado a True y registra el evento
        self.estado = True
        registrar_evento(f"[+] {self.nombre} -> Estado cambiado a: ENCENDIDO (ON)")

    def apagar(self):
        # Comportamiento genérico: solo cambia el estado a False y registra el evento
        self.estado = False
        registrar_evento(f"[-] {self.nombre} -> Estado cambiado a: APAGADO (OFF)")


class ActuadorProporcional(Actuador):
    """Actuador que opera en un rango analógico de 0% a 100%."""
    def __init__(self, nombre: str):
        # Se reutiliza el constructor de la clase base (Actuador) mediante super()
        super().__init__(nombre)
        self.rango_operacion_min = 0.0   
        self.rango_operacion_max = 100.0 
        # Punto de operación actual dentro del rango analógico (0.0 a 100.0)
        self.punto_operacion = 0.0       

    def ajustar(self, valor: float):
        # Se valida que el valor solicitado esté dentro del rango permitido (0% - 100%)
        if self.rango_operacion_min <= valor <= self.rango_operacion_max:
            self.punto_operacion = valor
            # Si el valor es mayor a 0, se considera "encendido"; si es 0, "apagado"
            if valor > 0:
                self.estado = True
            else:
                self.estado = False
            registrar_evento(f"[⚙] {self.nombre} -> Punto de operación ajustado al {self.punto_operacion:.1f}%")
        else:
            # Si el valor está fuera de rango, se registra un evento de error y no se aplica el cambio
            registrar_evento(f"[⚠️ ERROR] {self.nombre} -> Valor {valor}% fuera de rango (0% - 100%).")

    def info(self) -> str:
        # Genera una línea de texto formateada con el estado actual del actuador,
        # usada por la interfaz HMI para mostrar el panel de actuadores
        estado_str = "ON" if self.estado else "OFF"
        return f"{self.nombre:<20} | Estado: {estado_str:<3} | Punto Op: {self.punto_operacion:>5.1f}% | Rango: [0.0% - 100.0%]"


class ActuadorDigital(Actuador):
    """Actuador que opera de manera binaria (0 o 1)."""
    def __init__(self, nombre: str):
        super().__init__(nombre)
        # Valor lógico del actuador: 0 (apagado) o 1 (encendido)
        self.punto_operacion = 0

    def encender(self):
        # Se reutiliza el método encender() de la clase base (Actuador) y además
        # se actualiza el punto_operacion a 1, propio de este tipo de actuador
        super().encender()
        self.punto_operacion = 1

    def apagar(self):
        # Igual que encender(), pero fijando punto_operacion en 0
        super().apagar()
        self.punto_operacion = 0

    def ajustar(self, valor: float):
        # Solo acepta 0 o 1; internamente delega en encender()/apagar()
        if valor == 1:
            self.encender()
        elif valor == 0:
            self.apagar()
        else:
            # Cualquier otro valor se considera inválido para un actuador digital
            registrar_evento(f"[⚠️ ERROR] {self.nombre} -> Es digital. Solo acepta valores de 0 o 1.")

    def info(self) -> str:
        # Línea de texto formateada para el panel de actuadores (versión digital)
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
        # Valor dinámico interno para simulación del proceso
        # Se inicializa en un punto intermedio del rango (aprox. un tercio entre min y max)
        self.valor_actual = round((rango_min + rango_max) / 3.0, decimales_medicion)

    def leer_valor_actual(self) -> float:
        # En variables no controladas directamente (presión) se añade ruido de proceso
        # Es decir: solo la temperatura se calcula mediante el modelo de control (ejecutar_modo_automatico);
        # cualquier otra variable (como la presión) se simula con un valor aleatorio en cada lectura
        if self.variable_fisica != "Temperatura":
            self.valor_actual = round(random.uniform(self.rango_min, self.rango_max * 0.5), self.decimales_medicion)
        
        lectura_str = f"{self.valor_actual:.{self.decimales_medicion}f} {self.unidad}"
        # Cada lectura del sensor queda registrada en el historial de eventos
        registrar_evento(f"[📊 LECTURA] {self.nombre}: {lectura_str} (Var: {self.variable_fisica})")
        return self.valor_actual

    def info(self) -> str:
        # Línea de texto formateada con las características estáticas del sensor,
        # usada en el panel de sensores de la interfaz HMI
        return f"{self.nombre:<20} | Var: {self.variable_fisica:<18} | Rango: [{self.rango_min:>4.1f} - {self.rango_max:>5.1f}] {self.unidad:<5} | Sensibilidad: {self.sensibilidad} | Dec: {self.decimales_medicion}"


# ==============================================================================
# CONTROL AUTOMÁTICO
# ==============================================================================
def ejecutar_modo_automatico(actuadores, sensores, consigna_temp=50.0):
    """
    Algoritmo de estabilidad dinámica:
    ΔT = (+1.5°C) - (0.05°C × % OperaciónBomba)
    """
    bomba = actuadores["bomba"]
    sensor_temp = sensores["termometro"]

    # Control proporcional simple hacia una temperatura objetivo segura (50.0 °C)
    # error > 0 significa que la temperatura actual está por encima de la consigna
    error = sensor_temp.valor_actual - consigna_temp
    # Punto de equilibrio base: 1.5 / 0.05 = 30.0%
    # A partir de ese punto de equilibrio, se suma una corrección proporcional al error
    nuevo_porcentaje = 30.0 + (error * 2.0)
    # Se limita el porcentaje resultante al rango físico válido de la bomba (0% - 100%)
    nuevo_porcentaje = max(0.0, min(100.0, nuevo_porcentaje))
    
    bomba.ajustar(nuevo_porcentaje)

    # Cálculo dinámico de ΔT según la fórmula: a mayor % de bomba, menor incremento de temperatura
    delta_t = 1.5 - (0.05 * bomba.punto_operacion)
    # Se actualiza la temperatura simulada del sensor sumando el ΔT calculado
    sensor_temp.valor_actual = round(sensor_temp.valor_actual + delta_t, sensor_temp.decimales_medicion)

    registrar_evento(f"[🤖 AUTO] Bomba al {bomba.punto_operacion:.1f}% | ΔT: {delta_t:+.2f}°C | Temp: {sensor_temp.valor_actual:.2f}°C")


# ==============================================================================
# RUTINA DE INYECCIÓN DE FALLOS (MODO PRUEBAS)
# ==============================================================================
def ejecutar_modo_pruebas(actuadores, sensores):
    """
    Rutina que inyecta fallos aleatorios en el sistema para validar
    límites operativos y mecanismos de seguridad del HMI.
    """
    # Se define el catálogo de posibles fallos a simular en cada ciclo
    fallos_posibles = ["sobrecalentamiento", "sobrepresion", "falla_bomba", "falla_valvula", "sin_novedad"]
    # Se elige uno al azar en cada llamada a esta función
    fallo = random.choice(fallos_posibles)

    if fallo == "sobrecalentamiento":
        # Fuerza la temperatura por encima de los 150.0 °C
        # (esto es mayor al límite normal del sensor, para probar el interlock de seguridad)
        temp_critica = round(random.uniform(151.0, 180.0), sensores["termometro"].decimales_medicion)
        sensores["termometro"].valor_actual = temp_critica
        registrar_evento(f"[🔥 ALERTA PRUEBA] Límite térmico excedido. Temp inyectada: {temp_critica} °C")

    elif fallo == "sobrepresion":
        # Fuerza la presión por encima de los 15.0 Bar
        # (por encima del rango nominal del sensor, también para probar el interlock)
        pres_critica = round(random.uniform(15.5, 25.0), sensores["presion"].decimales_medicion)
        sensores["presion"].valor_actual = pres_critica
        registrar_evento(f"[💥 ALERTA PRUEBA] Límite barométrico excedido. Presión inyectada: {pres_critica} Bar")

    elif fallo == "falla_bomba":
        # Envía un valor inválido a la bomba de enfriamiento (> 100%)
        # para comprobar que ActuadorProporcional.ajustar() rechace valores fuera de rango
        falla_porcentaje = round(random.uniform(105.0, 150.0), 1)
        registrar_evento("[⚙️ PRUEBA] Inyectando fallo: Intentando modular bomba fuera de límite...")
        actuadores["bomba"].ajustar(falla_porcentaje)

    elif fallo == "falla_valvula":
        # Envía un valor lógico inválido a la válvula digital (diferente de 0 o 1)
        # para comprobar que ActuadorDigital.ajustar() rechace valores no binarios
        falla_logica = random.choice([-1, 2, 5, 9])
        registrar_evento("[🚰 PRUEBA] Inyectando fallo: Valor lógico no reconocido en válvula...")
        actuadores["valvula"].ajustar(falla_logica)
    
    elif fallo == "sin_novedad":
        # Caso en el que no se inyecta ningún fallo durante este ciclo
        registrar_evento("[🧪 PRUEBA] Monitoreo estable. Sin anomalías inyectadas en este ciclo.")


# ==============================================================================
# [!WARNING] INTERLOCKS DE SEGURIDAD (PRIORIDAD MÁXIMA DE EJECUCIÓN)
# ==============================================================================
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

    # Se comprueba si alguna de las dos variables críticas superó su umbral de seguridad
    if temp > 85.0 or pres > 12.0:
        bomba = actuadores["bomba"]
        valvula = actuadores["valvula"]

        # Se fuerza la bomba al 100% solo si no está ya en ese valor (evita eventos repetidos)
        if bomba.punto_operacion != 100.0:
            bomba.ajustar(100.0)
        # Se fuerza la apertura total de la válvula solo si no está ya abierta
        if valvula.punto_operacion != 1:
            valvula.encender()

        registrar_evento(
            f"[🚨 INTERLOCK] Condición crítica (T={temp:.2f}°C, P={pres:.2f}Bar) -> "
            f"Bomba forzada 100% / Válvula ABIERTA. Control del operario BLOQUEADO."
        )
        # Se indica al bucle principal que el interlock está activo (bloquea comandos manuales)
        return True

    # Si ninguna variable supera su umbral, no hay condición crítica activa
    return False


# ==============================================================================
# INTERFAZ HMI (TABLERO DE CONTROL)
# ==============================================================================
def mostrar_interfaz_hmi(actuadores, sensores, modo_operacion, interlock_activo=False):
    # Encabezado del panel, indicando el modo de operación actual
    print("=" * 95)
    print(f"            PANEL DE CONTROL INDUSTRIAL HMI - MODO: [{modo_operacion.upper()}]")
    if interlock_activo:
        # Aviso visual centrado cuando el interlock de seguridad está activo
        print(" 🚨 INTERLOCK DE SEGURIDAD ACTIVO - CONTROL DEL OPERARIO BLOQUEADO 🚨".center(95))
    print("=" * 95)
    
    # Sección de actuadores: recorre el diccionario e imprime la info() de cada uno
    print(" [ACTUADORES]")
    for key, act in actuadores.items():
        print(f"   ► [{key:<7}] {act.info()}")
    print("-" * 95)
    
    # Sección de sensores: recorre el diccionario e imprime la info() más la lectura actual
    print(" [SENSORES]")
    for key, sen in sensores.items():
        print(f"   ► [{key:<10}] {sen.info()} | Lectura: {sen.valor_actual} {sen.unidad}")
    print("=" * 95)
    
    # Sección de eventos recientes (los últimos 5 registrados en historial_eventos)
    print(" [REGISTRO DE EVENTOS EN VIVO (SCADA/HMI)]")
    if not historial_eventos:
        print("   (Sin actividad reciente)")
    else:
        for ev in historial_eventos:
            print(f"   {ev}")
    print("=" * 95)
    
    # Ayuda de comandos disponibles para el operario
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


# ==============================================================================
# BUCLE INTERACTIVO PRINCIPAL
# ==============================================================================
def main():
    # Instancias de los dos actuadores del sistema
    Bomba_de_Enfriamiento = ActuadorProporcional("Bomba de Enfriamiento")
    Valvula_de_Alivio = ActuadorDigital("Válvula de Alivio")

    # Instancia del sensor de temperatura, con valor inicial forzado a 0
    termometro = Sensor("Termometro", "Temperatura", 0.0, 150.0, 0.01, 3, "°C")
    termometro.valor_actual = 0
    # Instancia del sensor de presión (usa el valor inicial calculado en el constructor)
    presion = Sensor("Presion", "Presion", 0.0, 15.0, 0.001, 2, "Bar")

    # Diccionarios de acceso rápido a actuadores y sensores por nombre clave
    actuadores = {"bomba": Bomba_de_Enfriamiento, "valvula": Valvula_de_Alivio}
    sensores = {"termometro": termometro, "presion": presion}

    # Estado inicial del sistema: modo manual, sin interlock activo
    modo_operacion = "MANUAL"
    interlock_activo = False

    while True:
        # Ejecución de los modos automatizados por ciclo
        # (en modo MANUAL no se ejecuta ninguna lógica automática adicional)
        if modo_operacion == "AUTO":
            ejecutar_modo_automatico(actuadores, sensores)
        elif modo_operacion == "PRUEBAS":
            ejecutar_modo_pruebas(actuadores, sensores)

        # [!WARNING] Interlock de seguridad: se evalúa siempre, con prioridad
        # sobre cualquier modo, y puede sobrescribir lo calculado arriba.
        interlock_activo = verificar_interlocks_seguridad(actuadores, sensores)

        # Se refresca la pantalla y se dibuja el panel HMI actualizado
        limpiar_pantalla()
        mostrar_interfaz_hmi(actuadores, sensores, modo_operacion, interlock_activo)
        
        # Lectura del comando ingresado por el operario, con manejo de Ctrl+C / EOF
        try:
            entrada = input("Ingrese comando >> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n[+] Programa terminado.")
            break

        # Si el usuario no escribió nada, se vuelve a mostrar el panel sin procesar comando
        if not entrada:
            continue

        # Comando de salida del programa
        if entrada.lower() == "terminar":
            print("\n[+] Cerrando sistema de control... Programa finalizado con éxito.")
            break

        # Se separa la entrada en palabras (comando + argumentos)
        partes = entrada.split()
        if len(partes) == 0:
            continue

        comando = partes[0].lower()

        # --- Cambio de Modo de Operación ---
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

        # --- Comando: encender un actuador ---
        elif comando == "encender":
            # Bloqueado si hay un interlock de seguridad activo
            if interlock_activo:
                registrar_evento("[⚠️ DENEGADO] Interlock de seguridad activo. Control manual bloqueado.")
                continue
            # Bloqueado si el sistema está en modo automático (el control es del algoritmo, no del operario)
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

        # --- Comando: apagar un actuador ---
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

        # --- Comando: ajustar un actuador a un valor numérico ---
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
                # Se intenta convertir el tercer argumento a número decimal
                valor = float(partes[2])
                if target in actuadores:
                    actuadores[target].ajustar(valor)
                else:
                    registrar_evento(f"[⚠️ ERROR] Actuador '{target}' no existe. Opciones: bomba, valvula")
            except ValueError:
                # Si la conversión falla, el valor ingresado no era numérico
                registrar_evento("[⚠️ ERROR] El valor de ajuste debe ser numérico.")

        # --- Comando: leer el valor actual de un sensor ---
        elif comando == "leer":
            if len(partes) < 2:
                registrar_evento("[⚠️ ERROR] Especifica el sensor. Uso: leer <termometro/presion>")
                continue
            target = partes[1].lower()
            if target in sensores:
                sensores[target].leer_valor_actual()
            else:
                registrar_evento(f"[⚠️ ERROR] Sensor '{target}' no existe. Opciones: termometro, presion")

        # --- Comando no reconocido ---
        else:
            registrar_evento(f"[⚠️ ERROR] Comando '{comando}' no reconocido.")

# Punto de entrada del script: solo se ejecuta main() si el archivo se corre directamente
# (no si se importa como módulo desde otro archivo)
if __name__ == "__main__":
    main()
