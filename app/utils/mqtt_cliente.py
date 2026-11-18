"""
Conexión MQTT del Rincón Lector (compartida por todas las páginas).

El cliente se crea una sola vez (st.cache_resource) y se queda escuchando en
segundo plano (loop_start). Lo que llega desde el tótem de Wokwi se guarda en
un diccionario de estado que las páginas consultan cada pocos segundos.
"""

import random
import threading
import time

import paho.mqtt.client as mqtt
import streamlit as st

BROKER = "broker.hivemq.com"
PUERTO = 1883

PREFIJO = "rinconlector_mac"
TOPIC_LIBRO = f"{PREFIJO}/libro"      # App -> tótem: "titulo|genero|idioma" o "ninguno"
TOPIC_LAMPARA = f"{PREFIJO}/lampara"  # App -> tótem: brillo 0-100
TOPIC_FIN = f"{PREFIJO}/fin"          # App -> tótem: "tocar"
TOPIC_BOTON = f"{PREFIJO}/boton"      # Tótem -> app: "leer"
TOPIC_LUZ = f"{PREFIJO}/luz"          # Tótem -> app: luz 0-100

# Si no llega la luz del LDR en este tiempo, el tótem se considera desconectado
# (20 s porque Wokwi puede correr lento y enviar la luz con retraso)
SEGUNDOS_SIN_SENAL = 20


class ConexionTotem:
    """Guarda el cliente MQTT y lo último que ha enviado el tótem."""

    def __init__(self):
        self._lock = threading.Lock()
        self.estado = {
            "conectado_broker": False,
            "luz": None,             # último nivel de luz recibido (0-100)
            "ultima_senal": 0.0,     # momento del último mensaje del tótem
            "pulsaciones": 0,        # contador de veces que se presionó "Léemelo"
            "ultima_pulsacion": 0.0,
        }

        client_id = f"rinconlector-app-{random.randint(0, 999999)}"
        self.cliente = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )
        self.cliente.on_connect = self._al_conectar
        self.cliente.on_disconnect = self._al_desconectar
        self.cliente.on_message = self._al_recibir
        self.cliente.reconnect_delay_set(min_delay=1, max_delay=10)

        # connect_async no bloquea la app si el broker tarda en responder
        self.cliente.connect_async(BROKER, PUERTO, keepalive=30)
        self.cliente.loop_start()

    # ---------- Callbacks de paho ----------
    def _al_conectar(self, cliente, userdata, flags, reason_code, properties):
        with self._lock:
            self.estado["conectado_broker"] = not reason_code.is_failure
        cliente.subscribe([(TOPIC_BOTON, 0), (TOPIC_LUZ, 0)])

    def _al_desconectar(self, cliente, userdata, flags, reason_code, properties):
        with self._lock:
            self.estado["conectado_broker"] = False

    def _al_recibir(self, cliente, userdata, mensaje):
        texto = mensaje.payload.decode("utf-8", errors="ignore").strip()
        ahora = time.time()
        with self._lock:
            self.estado["ultima_senal"] = ahora
            if mensaje.topic == TOPIC_LUZ:
                try:
                    self.estado["luz"] = max(0, min(100, int(texto)))
                except ValueError:
                    pass
            elif mensaje.topic == TOPIC_BOTON and texto == "leer":
                self.estado["pulsaciones"] += 1
                self.estado["ultima_pulsacion"] = ahora

    # ---------- Uso desde las páginas ----------
    def leer_estado(self):
        with self._lock:
            return dict(self.estado)

    def totem_en_linea(self):
        estado = self.leer_estado()
        return (time.time() - estado["ultima_senal"]) < SEGUNDOS_SIN_SENAL

    def publicar(self, topic, mensaje, retener=False):
        """
        Envía un mensaje al tótem. Devuelve True si se pudo enviar.

        retener=True guarda el mensaje en el broker: si el tótem se desconecta
        y vuelve a conectarse (o se reinicia la simulación), recibe de una vez
        el último libro y el último brillo de la lámpara.
        """
        if not self.cliente.is_connected():
            return False
        resultado = self.cliente.publish(topic, str(mensaje), qos=1, retain=retener)
        return resultado.rc == mqtt.MQTT_ERR_SUCCESS

    def enviar_libro(self, libro):
        return self.publicar(
            TOPIC_LIBRO,
            f"{libro['titulo_lcd']}|{libro['genero']}|{libro['idioma']}",
            retener=True,
        )

    def limpiar_totem(self):
        return self.publicar(TOPIC_LIBRO, "ninguno", retener=True)

    def enviar_lampara(self, nivel):
        return self.publicar(TOPIC_LAMPARA, int(max(0, min(100, nivel))), retener=True)

    def tocar_melodia(self):
        return self.publicar(TOPIC_FIN, "tocar")


@st.cache_resource
def obtener_conexion():
    """Crea la conexión una sola vez y la comparte entre páginas y recargas."""
    return ConexionTotem()
