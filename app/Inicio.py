"""
RINCÓN LECTOR · Página de inicio
Proyecto final - Interfaces Multimodales
"""

import streamlit as st

from utils.estilo import aplicar_estilo
from utils.mqtt_cliente import obtener_conexion

st.set_page_config(page_title="Rincón Lector", page_icon="📚", layout="centered")
aplicar_estilo()

conexion = obtener_conexion()

st.title("📚 Rincón Lector")
st.markdown(
    "#### Libros que se ven, se escuchan, se dibujan y se sienten.\n"
    "Un rincón de lectura para todas las personas: niños que empiezan a leer, "
    "adultos mayores y quienes no leen con facilidad. Solo necesitas mostrar un "
    "libro a la cámara y apretar un botón."
)

st.divider()

# ---------- Cómo funciona ----------
st.subheader("¿Cómo funciona?")
col1, col2, col3 = st.columns(3)
pasos = [
    ("📷", "1. Muestra el libro", "Pon la portada frente a la cámara."),
    ("💡", "2. El tótem se ilumina", "La pantalla muestra el título y la luz cambia de color."),
    ("🔊", "3. Aprieta «Léemelo»", "Te cuento de qué trata el libro en voz alta."),
]
for col, (icono, titulo, texto) in zip((col1, col2, col3), pasos):
    col.markdown(
        f'<div class="paso"><div class="icono">{icono}</div>'
        f'<div class="titulo">{titulo}</div><div>{texto}</div></div>',
        unsafe_allow_html=True,
    )

st.divider()


# ---------- Estado del tótem (se actualiza solo cada 3 s) ----------
@st.fragment(run_every=3)
def estado_totem():
    estado = conexion.leer_estado()
    if conexion.totem_en_linea():
        luz = estado["luz"]
        st.success(f"🟢 **Tótem conectado** · luz en la mesa: {luz} %", icon=None)
    elif estado["conectado_broker"]:
        st.warning(
            "🟡 **La app está lista, pero el tótem no responde.** "
            "Abre la simulación de Wokwi y dale ▶️."
        )
    else:
        st.error("🔴 **Conectando con el servidor MQTT…** Espera unos segundos.")


st.subheader("Estado del tótem")
estado_totem()

st.divider()

# ---------- Ir a los ambientes ----------
st.subheader("Elige un ambiente")
izq, der = st.columns(2)
with izq:
    st.markdown("**📚 Rincón de descubrimiento**  \nMuestra un libro y escucha de qué trata.")
    st.page_link("pages/1_📚_Descubrimiento.py", label="Ir a Descubrimiento", icon="➡️")
with der:
    st.markdown("**🛋️ Sala de lectura**  \nAjusta la luz con tu voz y deja tu reseña.")
    st.caption("Próximamente")

st.divider()
st.caption(
    "Proyecto final · Interfaces Multimodales · María Alejandra Cisneros · "
    "[Simulación del tótem en Wokwi](https://wokwi.com/projects/481061636688423937)"
)
