"""
Voz del Rincón Lector: hablar (texto a voz) y escuchar (voz a texto).

- Texto a voz: gTTS (Google Text-to-Speech).
- Voz a texto: SpeechRecognition con el reconocedor gratuito de Google,
  a partir del audio WAV que graba st.audio_input en el navegador.
"""

import base64
import io
import time

import speech_recognition as sr
import streamlit as st
from gtts import gTTS

# Idioma del reconocedor de voz según el idioma del libro
IDIOMA_RECONOCEDOR = {"es": "es-CO", "en": "en-US"}


@st.cache_data(show_spinner=False)
def generar_audio(texto: str, idioma: str) -> bytes:
    """Convierte un texto en audio MP3 (se guarda en caché para no repetir)."""
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


def hablar(texto: str, idioma: str, mostrar_reproductor=True) -> bool:
    """Genera y reproduce la voz. Devuelve False si no se pudo generar."""
    try:
        audio = generar_audio(texto, idioma)
    except Exception:
        st.error("😕 No pude generar la voz en este momento (revisa la conexión a internet).")
        return False
    reproducir(audio)
    if mostrar_reproductor:
        with st.expander("🎧 Reproductor (para pausar o repetir)"):
            st.audio(audio, format="audio/mp3")
    return True


def transcribir(audio_wav: bytes, idioma: str = "es"):
    """
    Convierte una grabación de voz en texto.
    Devuelve (texto, error): uno de los dos es None.
    """
    reconocedor = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(audio_wav)) as fuente:
            audio = reconocedor.record(fuente)
        texto = reconocedor.recognize_google(
            audio, language=IDIOMA_RECONOCEDOR.get(idioma, "es-CO")
        )
        return texto, None
    except sr.UnknownValueError:
        return None, "No te entendí. Intenta hablar más cerca del micrófono."
    except sr.RequestError:
        return None, "No me pude conectar al servicio de voz. Revisa la conexión a internet."
    except Exception:
        return None, "No pude procesar el audio. Intenta grabar de nuevo."
