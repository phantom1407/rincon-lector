"""
Reconocimiento de portadas con el modelo de Teachable Machine (Keras .h5).

El preprocesamiento es el mismo que usa Teachable Machine: recortar la imagen
a 224x224 y normalizar los píxeles al rango [-1, 1].
"""

from pathlib import Path

import numpy as np
import streamlit as st
from PIL import Image, ImageOps

CARPETA_MODELO = Path(__file__).resolve().parent.parent / "modelo"
RUTA_MODELO = CARPETA_MODELO / "keras_model.h5"
RUTA_ETIQUETAS = CARPETA_MODELO / "labels.txt"
TAMANO = (224, 224)


@st.cache_resource(show_spinner="Cargando el modelo de portadas…")
def cargar_modelo():
    # Se importa aquí para que las páginas que no usan el modelo carguen rápido
    from tensorflow.keras.models import load_model

    modelo = load_model(str(RUTA_MODELO), compile=False)
    etiquetas = []
    for linea in RUTA_ETIQUETAS.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea:
            # Cada línea viene como "0 lobo_estepario_es"
            partes = linea.split(" ", 1)
            etiquetas.append(partes[1] if len(partes) == 2 else partes[0])
    return modelo, etiquetas


def preparar_imagen(imagen: Image.Image) -> np.ndarray:
    imagen = ImageOps.exif_transpose(imagen).convert("RGB")
    imagen = ImageOps.fit(imagen, TAMANO, Image.Resampling.LANCZOS)
    arreglo = np.asarray(imagen, dtype=np.float32)
    arreglo = (arreglo / 127.5) - 1.0
    return np.expand_dims(arreglo, axis=0)


def reconocer(imagen: Image.Image):
    """Devuelve (clase_ganadora, confianza, {clase: probabilidad})."""
    modelo, etiquetas = cargar_modelo()
    probabilidades = modelo.predict(preparar_imagen(imagen), verbose=0)[0]
    indice = int(np.argmax(probabilidades))
    todas = {etiquetas[i]: float(p) for i, p in enumerate(probabilidades)}
    return etiquetas[indice], float(probabilidades[indice]), todas
