"""
RINCÓN LECTOR · Página 2: Sala de lectura
Modalidades: voz de entrada (comandos y reseña dictada), texto, dibujo,
toque (caritas, interruptor y deslizador), sensor de luz (LDR) y actuadores
del tótem (lámpara y buzzer), más voz de salida para la recomendación.
"""

import hashlib
import io
from datetime import datetime

import numpy as np
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas

from utils.estilo import aplicar_estilo, chip
from utils.lenguaje import clasificar_gusto, describir_luz, interpretar_comando, nivel_automatico
from utils.libros import LIBROS, RECOMENDACIONES, texto_recomendacion
from utils.mqtt_cliente import obtener_conexion
from utils.voz import hablar, transcribir

st.set_page_config(page_title="Sala de lectura · Rincón Lector", page_icon="💡", layout="centered")
aplicar_estilo()

conexion = obtener_conexion()

# ---------- Estado de la sesión ----------
valores_iniciales = {
    "lampara": 0,                 # brillo actual de la lámpara (0-100)
    "modo_auto": False,           # lámpara automática según la luz del cuarto
    "audio_luz_visto": None,      # hash del último comando de voz procesado
    "ultimo_comando": None,       # (lo que se escuchó, lo que se hizo)
    "audio_resena_visto": None,   # hash de la última reseña dictada
    "texto_resena": "",           # texto de la reseña (dictado o escrito)
    "dibujo_json": None,          # trazos del tablero (para no perderlos)
    "dibujo_png": None,           # imagen del dibujo
    "aviso_resena": False,
    "celebrar": False,
    "resena_n": 0,                # cambia las keys para empezar una reseña nueva
    "ultima_resena": None,        # resultado de la última reseña guardada
    "hablar_recomendacion": False,
    "resenas": [],                # historial de reseñas de esta sesión
}
for clave, valor in valores_iniciales.items():
    st.session_state.setdefault(clave, valor)


def cambiar_lampara(nivel: int):
    nivel = int(max(0, min(100, nivel)))
    st.session_state.lampara = nivel
    conexion.enviar_lampara(nivel)


# ============================================================
#  PARTE A · La luz para leer
# ============================================================
st.title("💡 Sala de lectura")
st.markdown("Ajusta la luz de tu mesa y, cuando termines el libro, cuéntanos qué te pareció.")

st.header("1. La luz para leer")
zona_medidor = st.container()  # aquí se dibuja el medidor en vivo (más abajo)

# --- Control por voz ---
st.markdown("**🎤 Dile a la lámpara qué hacer**  \n"
            "Por ejemplo: *«más luz»*, *«menos luz»*, *«luz al 50»*, *«apaga la luz»*, "
            "*«modo automático»* · *«more light»*, *«turn off»*.")
idioma_voz = st.radio(
    "Idioma de tu voz", options=["es", "en"], horizontal=True, key="idioma_voz",
    format_func=lambda x: "🇪🇸 Español" if x == "es" else "🇬🇧 English",
)
grabacion_luz = st.audio_input("Graba tu orden", key="audio_luz")

if grabacion_luz is not None:
    datos = grabacion_luz.getvalue()
    huella = hashlib.md5(datos).hexdigest()
    if huella != st.session_state.audio_luz_visto:
        st.session_state.audio_luz_visto = huella
        with st.spinner("Escuchando…"):
            texto, error = transcribir(datos, idioma_voz)
        if error:
            st.session_state.ultimo_comando = (None, error)
        else:
            accion, nivel, explicacion = interpretar_comando(texto, st.session_state.lampara)
            if accion == "auto":
                st.session_state.modo_auto = True
            elif accion == "nivel":
                st.session_state.modo_auto = False
                cambiar_lampara(nivel)
            st.session_state.ultimo_comando = (
                texto, explicacion or "No entendí la orden. Prueba con «más luz» o «luz al 50»."
            )

if st.session_state.ultimo_comando:
    escuchado, resultado = st.session_state.ultimo_comando
    if escuchado:
        st.success(f"Escuché: «{escuchado}» → **{resultado}**")
    else:
        st.warning(resultado)

# --- Control manual ---
st.toggle(
    "🤖 Modo automático (la lámpara se ajusta sola según la luz del cuarto)",
    key="modo_auto",
)
if not st.session_state.modo_auto:
    nivel_manual = st.slider(
        "O muévela a mano", 0, 100, value=st.session_state.lampara, step=5, format="%d %%"
    )
    if nivel_manual != st.session_state.lampara:
        cambiar_lampara(nivel_manual)


# --- Medidor en vivo (se actualiza solo cada 2 s) ---
@st.fragment(run_every=2)
def medidor_luz():
    en_linea = conexion.totem_en_linea()
    luz = conexion.leer_estado()["luz"] if en_linea else None

    if st.session_state.modo_auto and luz is not None:
        objetivo = nivel_automatico(luz)
        if objetivo != st.session_state.lampara:
            cambiar_lampara(objetivo)

    icono, mensaje = describir_luz(luz)
    col_luz, col_lampara = st.columns(2)
    col_luz.metric("☀️ Luz en la mesa (sensor)", f"{luz} %" if luz is not None else "—")
    modo = "automática" if st.session_state.modo_auto else "manual"
    col_lampara.metric(f"💡 Lámpara ({modo})", f"{st.session_state.lampara} %")
    st.progress(luz / 100 if luz is not None else 0.0)
    st.markdown(f"#### {icono} {mensaje}")
    if not en_linea:
        st.caption("🔴 Tótem desconectado · abre la simulación de Wokwi y dale ▶️")


with zona_medidor:
    medidor_luz()

st.divider()

# ============================================================
#  PARTE B · Mi reseña
# ============================================================
st.header("2. Mi reseña")

claves_libros = list(LIBROS.keys())
libro_inicial = st.session_state.get("libro_clave") or claves_libros[0]
n = st.session_state.resena_n

clave_libro = st.selectbox(
    "¿Qué libro leíste?",
    options=claves_libros,
    index=claves_libros.index(libro_inicial),
    format_func=lambda k: f"{LIBROS[k]['emoji']} {LIBROS[k]['titulo']}",
    key=f"libro_resena_{n}",
)
libro = LIBROS[clave_libro]
en_ingles = libro["idioma"] == "en"

st.markdown("**¿Te gustó?** Toca una carita:")
carita = st.feedback("faces", key=f"carita_{n}")  # 0 (😞) a 4 (😍) o None

st.markdown("**Cuéntanos más** (como prefieras, puedes usar las tres):")
# Se usa un selector y no pestañas: el tablero de dibujo no se dibuja bien
# si se carga dentro de una pestaña oculta.
forma = st.radio(
    "Forma de contarlo",
    options=["voz", "texto", "dibujo"],
    format_func={"voz": "🎤 Dictar", "texto": "✍️ Escribir", "dibujo": "🎨 Dibujar"}.get,
    horizontal=True,
    key=f"forma_{n}",
    label_visibility="collapsed",
)

if forma == "voz":
    st.caption(f"Habla en {'inglés' if en_ingles else 'español'} y luego revisa el texto en «Escribir».")
    grabacion_resena = st.audio_input("Graba tu reseña", key=f"audio_resena_{n}")
    if grabacion_resena is not None:
        datos = grabacion_resena.getvalue()
        huella = hashlib.md5(datos).hexdigest()
        if huella != st.session_state.audio_resena_visto:
            st.session_state.audio_resena_visto = huella
            with st.spinner("Escuchando tu reseña…"):
                texto, error = transcribir(datos, libro["idioma"])
            if error:
                st.warning(error)
            else:
                anterior = st.session_state.texto_resena.strip()
                st.session_state.texto_resena = f"{anterior} {texto}".strip()
    if st.session_state.texto_resena:
        st.success(f"Escuché: «{st.session_state.texto_resena}»")

elif forma == "texto":
    # Sin key: el texto se guarda aparte para no perderlo al cambiar de forma
    escrito = st.text_area(
        "Tu reseña", value=st.session_state.texto_resena, height=140,
        placeholder="Me gustó porque…" if not en_ingles else "I liked it because…",
    )
    st.session_state.texto_resena = escrito

else:
    st.caption("Dibuja lo que te imaginaste mientras leías.")
    col_color, col_grosor = st.columns(2)
    color = col_color.color_picker("Color", "#0F4C5C", key=f"color_{n}")
    grosor = col_grosor.slider("Grosor", 2, 20, 6, key=f"grosor_{n}")
    lienzo = st_canvas(
        fill_color="rgba(0,0,0,0)",
        stroke_width=grosor,
        stroke_color=color,
        background_color="#FFFFFF",
        height=300,
        width=600,
        drawing_mode="freedraw",
        initial_drawing=st.session_state.dibujo_json,  # recupera el dibujo al volver
        key=f"lienzo_{n}",
    )
    if lienzo.json_data and lienzo.json_data.get("objects"):
        st.session_state.dibujo_json = lienzo.json_data
        if lienzo.image_data is not None:
            imagen = Image.fromarray(lienzo.image_data.astype(np.uint8), "RGBA")
            buffer = io.BytesIO()
            imagen.save(buffer, format="PNG")
            st.session_state.dibujo_png = buffer.getvalue()

if st.session_state.texto_resena or st.session_state.dibujo_png:
    listo = []
    if st.session_state.texto_resena:
        listo.append("✍️ texto")
    if st.session_state.dibujo_png:
        listo.append("🎨 dibujo")
    st.caption("Tu reseña tiene: " + " · ".join(listo))


def guardar_resena(clave_libro, carita):
    """Se ejecuta una sola vez por clic (callback del botón)."""
    texto = st.session_state.texto_resena.strip()
    dibujo = st.session_state.dibujo_png
    if carita is None and not texto and not dibujo:
        st.session_state.aviso_resena = True
        return
    st.session_state.aviso_resena = False
    gusto, puntaje = clasificar_gusto(carita, texto)
    resena = {
        "libro": clave_libro,
        "carita": carita,
        "texto": texto,
        "dibujo": dibujo,
        "gusto": gusto,
        "puntaje": round(puntaje, 2),
        "recomendacion": RECOMENDACIONES[clave_libro][gusto],
        "hora": datetime.now().strftime("%H:%M"),
    }
    st.session_state.ultima_resena = resena
    st.session_state.resenas.append(resena)
    st.session_state.hablar_recomendacion = True
    st.session_state.celebrar = True
    conexion.tocar_melodia()  # 🎵 el tótem celebra el libro terminado


st.button(
    "💾 Guardar reseña", type="primary", use_container_width=True,
    on_click=guardar_resena, args=(clave_libro, carita),
)
if st.session_state.aviso_resena:
    st.warning("Toca una carita, escribe, dicta o dibuja algo antes de guardar. 🙂")
if st.session_state.celebrar:
    st.session_state.celebrar = False
    st.balloons()

# ---------- Resultado y recomendación ----------
resena = st.session_state.ultima_resena
if resena is not None:
    libro_r = LIBROS[resena["libro"]]
    reco = resena["recomendacion"]
    ingles = libro_r["idioma"] == "en"

    etiquetas = {
        "positivo": ("😍 Te gustó" if not ingles else "😍 You liked it", "#2A9D8F"),
        "neutral": ("🙂 Te pareció normal" if not ingles else "🙂 It was okay for you", "#E9A23B"),
        "negativo": ("🙁 No te convenció" if not ingles else "🙁 It wasn't for you", "#E63946"),
    }
    texto_gusto, color_gusto = etiquetas[resena["gusto"]]

    st.subheader("¡Gracias por tu reseña!" if not ingles else "Thanks for your review!")
    st.markdown(chip(texto_gusto, color_gusto), unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="tarjeta-libro" style="border-top: 8px solid {libro_r['color']}">
          <div class="meta">{'Tu próxima lectura' if not ingles else 'Your next book'}</div>
          <h2>📖 {reco['titulo']}</h2>
          <div class="meta">{reco['autor']} · {reco['anio']}</div>
          <div class="resumen">{reco['por_que']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.session_state.hablar_recomendacion:
        st.session_state.hablar_recomendacion = False
        hablar(texto_recomendacion(libro_r, reco), libro_r["idioma"])

    def nueva_resena():
        st.session_state.resena_n += 1
        st.session_state.texto_resena = ""
        st.session_state.dibujo_json = None
        st.session_state.dibujo_png = None
        st.session_state.ultima_resena = None
        st.session_state.audio_resena_visto = None

    st.button("📝 Escribir otra reseña", on_click=nueva_resena, use_container_width=True)

# ---------- Historial ----------
if st.session_state.resenas:
    with st.expander(f"📒 Mis reseñas ({len(st.session_state.resenas)})"):
        caras = ["😞", "🙁", "😐", "🙂", "😍"]
        for r in reversed(st.session_state.resenas):
            cara = caras[r["carita"]] if r["carita"] is not None else "—"
            st.markdown(
                f"**{LIBROS[r['libro']]['titulo']}** · {cara} · {r['hora']}  \n"
                f"{r['texto'] or '_Sin texto_'}  \n"
                f"➡️ Recomendado: *{r['recomendacion']['titulo']}*"
            )
            if r["dibujo"]:
                st.image(r["dibujo"], width=300)
            st.divider()
