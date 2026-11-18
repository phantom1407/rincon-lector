"""
RINCÓN LECTOR · Página 1: Rincón de descubrimiento
Modalidades: imagen (cámara + modelo), voz de salida (gTTS) y botón físico del tótem.
"""

import base64
import hashlib
import io
import time

import streamlit as st
from gtts import gTTS
from PIL import Image

from utils.estilo import aplicar_estilo, chip
from utils.libros import CLASE_SIN_LIBRO, LIBROS, UMBRAL_CONFIANZA, texto_para_leer
from utils.modelo import reconocer
from utils.mqtt_cliente import obtener_conexion

st.set_page_config(page_title="Descubrimiento · Rincón Lector", page_icon="📚", layout="centered")
aplicar_estilo()

conexion = obtener_conexion()

# ---------- Estado de la sesión ----------
valores_iniciales = {
    "libro_clave": None,        # clase reconocida (clave de LIBROS) o None
    "confianza": 0.0,
    "probabilidades": {},
    "ultima_imagen": None,      # hash de la última foto procesada
    "camara_n": 0,              # cambia la key de la cámara para limpiarla
    "leer_ahora": False,        # True cuando hay que reproducir la voz
    "pulsaciones_vistas": None, # contador del botón físico ya atendido
    "mensaje": None,            # aviso corto para mostrar arriba
}
for clave, valor in valores_iniciales.items():
    st.session_state.setdefault(clave, valor)

if st.session_state.pulsaciones_vistas is None:
    # Ignorar pulsaciones que ocurrieron antes de abrir la página
    st.session_state.pulsaciones_vistas = conexion.leer_estado()["pulsaciones"]


# ---------- Voz ----------
@st.cache_data(show_spinner=False)
def generar_audio(texto: str, idioma: str) -> bytes:
    buffer = io.BytesIO()
    gTTS(text=texto, lang=idioma, slow=False).write_to_fp(buffer)
    return buffer.getvalue()


def reproducir(audio: bytes):
    """Reproduce el audio automáticamente (con un id distinto cada vez para que suene de nuevo)."""
    b64 = base64.b64encode(audio).decode()
    marca = int(time.time() * 1000)
    st.markdown(
        f'<audio autoplay id="voz-{marca}" src="data:audio/mp3;base64,{b64}"></audio>',
        unsafe_allow_html=True,
    )


# ---------- Acciones ----------
def procesar_imagen(datos: bytes):
    huella = hashlib.md5(datos).hexdigest()
    if huella == st.session_state.ultima_imagen:
        return  # la misma foto: no volver a reconocer ni a enviar al tótem
    st.session_state.ultima_imagen = huella

    imagen = Image.open(io.BytesIO(datos))
    clase, confianza, probabilidades = reconocer(imagen)
    st.session_state.confianza = confianza
    st.session_state.probabilidades = probabilidades

    if clase in LIBROS and confianza >= UMBRAL_CONFIANZA:
        st.session_state.libro_clave = clase
        enviado = conexion.enviar_libro(LIBROS[clase])
        st.session_state.mensaje = None if enviado else "sin_totem"
    else:
        st.session_state.libro_clave = None
        conexion.limpiar_totem()
        st.session_state.mensaje = "no_reconocido"


def otro_libro():
    st.session_state.libro_clave = None
    st.session_state.ultima_imagen = None
    st.session_state.probabilidades = {}
    st.session_state.mensaje = None
    st.session_state.camara_n += 1
    conexion.limpiar_totem()


def pedir_lectura():
    st.session_state.leer_ahora = True


# ---------- Interfaz ----------
st.title("📚 Rincón de descubrimiento")
st.markdown("Muestra la **portada** del libro a la cámara y toma la foto.")

col_camara, col_resultado = st.columns([1, 1], gap="large")

with col_camara:
    foto = st.camera_input(
        "📷 Cámara",
        key=f"camara_{st.session_state.camara_n}",
        help="Pon la portada del libro frente a la cámara y presiona «Take photo».",
    )
    with st.expander("¿No funciona la cámara? Sube una foto"):
        archivo = st.file_uploader(
            "Foto de la portada", type=["jpg", "jpeg", "png"],
            key=f"archivo_{st.session_state.camara_n}",
        )

    imagen_entrada = foto if foto is not None else archivo
    if imagen_entrada is not None:
        with st.spinner("Mirando la portada…"):
            procesar_imagen(imagen_entrada.getvalue())

with col_resultado:
    clave = st.session_state.libro_clave

    if clave is None and st.session_state.mensaje == "no_reconocido":
        st.warning(
            "🤔 **No reconozco este libro.** Acércalo un poco más, que la portada "
            "se vea completa y con buena luz, y toma otra foto."
        )
    elif clave is None:
        st.info("👈 Cuando tomes la foto, aquí aparece el libro.")

    if clave is not None:
        libro = LIBROS[clave]
        st.markdown(
            f"""
            <div class="tarjeta-libro" style="border-top: 8px solid {libro['color']}">
              <h2>{libro['emoji']} {libro['titulo']}</h2>
              <div class="meta">{libro['autor']} · {libro['anio']}</div>
              {chip(libro['genero_nombre'], libro['color'])}{chip(libro['idioma_nombre'], '#0F4C5C')}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(f"Reconocido con {st.session_state.confianza:.0%} de confianza.")
        if st.session_state.mensaje == "sin_totem":
            st.caption("⚠️ No pude avisarle al tótem. Revisa que Wokwi esté corriendo.")

        etiqueta_boton = "🔊 Léemelo" if libro["idioma"] == "es" else "🔊 Read it to me"
        st.button(etiqueta_boton, on_click=pedir_lectura, type="primary", use_container_width=True)
        st.button("🔄 Otro libro", on_click=otro_libro, use_container_width=True)

# ---------- Resumen y voz ----------
if st.session_state.libro_clave is not None:
    libro = LIBROS[st.session_state.libro_clave]
    titulo_resumen = "¿De qué trata?" if libro["idioma"] == "es" else "What is it about?"
    st.subheader(titulo_resumen)
    st.markdown(f'<div class="tarjeta-libro resumen">{libro["resumen"]}</div>', unsafe_allow_html=True)

    try:
        audio = generar_audio(texto_para_leer(libro), libro["idioma"])
    except Exception:
        audio = None
        if st.session_state.leer_ahora:
            st.error("😕 No pude generar la voz en este momento (revisa la conexión a internet).")
        st.session_state.leer_ahora = False

    if audio is not None:
        if st.session_state.leer_ahora:
            st.session_state.leer_ahora = False
            reproducir(audio)
            st.toast("🔊 Leyendo en voz alta…")
        with st.expander("🎧 Reproductor (para pausar o repetir)"):
            st.audio(audio, format="audio/mp3")


# ---------- Botón físico del tótem (se revisa cada 2 s) ----------
@st.fragment(run_every=2)
def escuchar_boton_totem():
    estado = conexion.leer_estado()
    nuevas = estado["pulsaciones"] - st.session_state.pulsaciones_vistas
    if nuevas > 0:
        st.session_state.pulsaciones_vistas = estado["pulsaciones"]
        if st.session_state.libro_clave is not None:
            st.session_state.leer_ahora = True
            st.rerun()  # vuelve a dibujar toda la página para que suene la voz
        else:
            st.toast("👆 Primero muestra un libro a la cámara.")

    if conexion.totem_en_linea():
        st.caption(f"🟢 Tótem conectado · aprieta su botón rojo «Léemelo» · luz: {estado['luz']} %")
    else:
        st.caption("🔴 Tótem desconectado · abre la simulación de Wokwi y dale ▶️")


st.divider()
escuchar_boton_totem()

# ---------- Detalle técnico (útil para la sustentación) ----------
if st.session_state.probabilidades:
    with st.expander("🔍 ¿Qué vio el modelo?"):
        for clase, prob in sorted(st.session_state.probabilidades.items(), key=lambda x: -x[1]):
            nombre = LIBROS[clase]["titulo"] if clase in LIBROS else "Sin libro"
            st.progress(prob, text=f"{nombre}: {prob:.0%}")
