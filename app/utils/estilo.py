"""Estilo visual compartido: letra y botones grandes para que sea fácil de usar."""

import streamlit as st

CSS = """
<style>
html, body, [class*="css"] { font-size: 19px; }
h1 { font-size: 2.4rem !important; }
h2 { font-size: 1.8rem !important; }
h3 { font-size: 1.4rem !important; }

/* Botones grandes y redondeados */
.stButton > button, .stDownloadButton > button {
    font-size: 1.15rem;
    padding: 0.7rem 1.4rem;
    border-radius: 14px;
    font-weight: 600;
}

/* Tarjeta de libro */
.tarjeta-libro {
    border-radius: 18px;
    padding: 1.3rem 1.5rem;
    margin: 0.5rem 0 1rem 0;
    background: #FFFFFF;
    box-shadow: 0 4px 18px rgba(0,0,0,0.08);
    color: #1F2933;
}
.tarjeta-libro h2 { margin: 0 0 0.3rem 0; color: #0F4C5C; }
.tarjeta-libro .meta { color: #52606D; font-size: 1rem; margin-bottom: 0.8rem; }
.tarjeta-libro .resumen { font-size: 1.1rem; line-height: 1.6; }
.chip {
    display: inline-block;
    padding: 0.2rem 0.8rem;
    border-radius: 999px;
    color: #FFFFFF;
    font-size: 0.95rem;
    font-weight: 600;
    margin-right: 0.4rem;
}

/* Pasos de la página de inicio */
.paso {
    text-align: center;
    padding: 1rem 0.6rem;
    border-radius: 16px;
    background: #EEF5F6;
    color: #1F2933;
    height: 100%;
}
.paso .icono { font-size: 2.6rem; }
.paso .titulo { font-weight: 700; color: #0F4C5C; margin-top: 0.3rem; }
</style>
"""


def aplicar_estilo():
    st.markdown(CSS, unsafe_allow_html=True)


def chip(texto, color):
    return f'<span class="chip" style="background:{color}">{texto}</span>'
