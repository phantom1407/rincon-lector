"""
Interpretación de lo que dice o escribe la persona.

1. Comandos de voz para la lámpara ("más luz", "luz al 50", "turn off"...).
2. Análisis de sentimiento sencillo de la reseña, por palabras clave en
   español e inglés (no necesita internet ni modelos pesados).
"""

import re
import unicodedata

PASO_LUZ = 25  # cuánto sube o baja la lámpara con "más luz" / "menos luz"


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar palabras con facilidad."""
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


# ============================================================
#  1. Comandos de la lámpara
# ============================================================
PALABRAS_AUTO = ["automatico", "automatica", "automatic", "auto"]
PALABRAS_APAGAR = ["apaga", "apagar", "apague", "turn off", "off", "lights off"]
PALABRAS_ENCENDER = ["enciende", "encender", "prende", "prender", "turn on", "lights on", "on"]
PALABRAS_MAX = ["maximo", "maxima", "toda la luz", "full", "maximum", "max"]
PALABRAS_MAS = ["mas", "sube", "subir", "aumenta", "more", "brighter", "increase", "up"]
PALABRAS_MENOS = ["menos", "baja", "bajar", "disminuye", "less", "dimmer", "dim", "decrease", "down"]


def _contiene(texto: str, palabras) -> bool:
    for palabra in palabras:
        if re.search(rf"\b{re.escape(palabra)}\b", texto):
            return True
    return False


def interpretar_comando(texto: str, nivel_actual: int):
    """
    Devuelve (accion, nuevo_nivel, explicacion).
    accion: "nivel", "auto" o None si no se entendió el comando.
    """
    t = normalizar(texto)

    if _contiene(t, PALABRAS_AUTO):
        return "auto", nivel_actual, "Modo automático activado"

    numero = re.search(r"(\d{1,3})", t)
    if numero:
        nivel = max(0, min(100, int(numero.group(1))))
        return "nivel", nivel, f"Lámpara al {nivel} %"

    if _contiene(t, PALABRAS_APAGAR):
        return "nivel", 0, "Lámpara apagada"
    if _contiene(t, PALABRAS_MAX):
        return "nivel", 100, "Lámpara al máximo"
    if _contiene(t, PALABRAS_MENOS):
        nivel = max(0, nivel_actual - PASO_LUZ)
        return "nivel", nivel, f"Menos luz: {nivel} %"
    if _contiene(t, PALABRAS_MAS):
        nivel = min(100, nivel_actual + PASO_LUZ)
        return "nivel", nivel, f"Más luz: {nivel} %"
    if _contiene(t, PALABRAS_ENCENDER):
        return "nivel", 70, "Lámpara encendida (70 %)"

    return None, nivel_actual, None


def nivel_automatico(luz_ambiente: int) -> int:
    """Entre más oscuro esté el cuarto, más fuerte la lámpara."""
    if luz_ambiente is None:
        return 0
    return int(max(0, min(100, round((100 - luz_ambiente) / 10) * 10)))


def describir_luz(luz: int):
    """Mensaje para la persona según la luz del cuarto."""
    if luz is None:
        return "⏳", "Esperando la medición del tótem…"
    if luz < 30:
        return "🌙", "Muy oscuro para leer. Prende la lámpara."
    if luz < 60:
        return "🌤️", "Luz regular. Un poco más de lámpara te ayudará."
    return "☀️", "Buena luz para leer."


# ============================================================
#  2. Sentimiento de la reseña
# ============================================================
POSITIVAS = [
    # español
    "me gusto", "me encanto", "encanto", "genial", "hermoso", "hermosa", "increible",
    "bueno", "buena", "excelente", "interesante", "maravilloso", "maravillosa",
    "recomiendo", "lo ame", "fascino", "emocionante", "lindo", "linda", "divertido",
    "divertida", "precioso", "brillante", "atrapante", "favorito", "favorita",
    # inglés
    "loved", "love", "great", "amazing", "good", "excellent", "interesting",
    "beautiful", "liked", "recommend", "awesome", "fun", "favorite", "brilliant",
    "exciting", "wonderful", "enjoyed",
]
NEGATIVAS = [
    # español
    "no me gusto", "no me encanto", "aburrido", "aburrida", "malo", "mala", "odie",
    "lento", "lenta", "confuso", "confusa", "pesado", "pesada", "terrible",
    "horrible", "no lo recomiendo", "no entendi", "largo", "larga",
    # inglés
    "didn't like", "did not like", "boring", "bad", "hated", "hate", "slow",
    "confusing", "terrible", "awful", "not good", "don't recommend",
]


def puntaje_texto(texto: str) -> float:
    """Puntaje entre -1 (negativo) y 1 (positivo) según las palabras de la reseña."""
    if not texto:
        return 0.0
    t = normalizar(texto)
    negativos = 0
    for frase in NEGATIVAS:
        if re.search(rf"\b{re.escape(normalizar(frase))}\b", t):
            negativos += 1
            t = re.sub(rf"\b{re.escape(normalizar(frase))}\b", " ", t)  # que "no me gusto" no cuente como "me gusto"
    positivos = sum(
        1 for frase in POSITIVAS if re.search(rf"\b{re.escape(normalizar(frase))}\b", t)
    )
    total = positivos + negativos
    return 0.0 if total == 0 else (positivos - negativos) / total


def clasificar_gusto(carita, texto: str):
    """
    Combina la carita (0 a 4, de 😞 a 😍) y el texto de la reseña.
    Devuelve ("positivo" | "neutral" | "negativo", puntaje).
    """
    partes = []
    if carita is not None:
        partes.append((carita - 2) / 2)  # 0..4 -> -1..1
    if texto and texto.strip():
        partes.append(puntaje_texto(texto))
    puntaje = sum(partes) / len(partes) if partes else 0.0
    if puntaje > 0.2:
        return "positivo", puntaje
    if puntaje < -0.2:
        return "negativo", puntaje
    return "neutral", puntaje
