"""
Catálogo del Rincón Lector.

Las claves son exactamente los nombres de las clases del modelo de
Teachable Machine (modelo/labels.txt). Los resúmenes son propios, escritos
para el proyecto (no son la contraportada de los libros).
"""

LIBROS = {
    "lobo_estepario_es": {
        "titulo": "El lobo estepario",
        "titulo_lcd": "El lobo estepario",  # sin tildes: la LCD no las muestra
        "autor": "Hermann Hesse",
        "anio": 1927,
        "idioma": "es",
        "idioma_nombre": "Español",
        "genero": "filosofia",
        "genero_nombre": "Filosofía e introspección",
        "color": "#7B2FF7",          # morado, igual que el LED del tótem
        "color_nombre": "morado",
        "emoji": "🐺",
        "resumen": (
            "Harry Haller es un hombre solitario de casi cincuenta años que siente "
            "que dentro de él viven dos almas: la de un caballero culto y tranquilo, "
            "y la de un lobo salvaje que desprecia a la sociedad. Una noche conoce a "
            "Hermine, una joven misteriosa que lo saca de su encierro y lo lleva a "
            "bailar, a reír y a mirar la vida de otra manera. La novela termina en el "
            "Teatro Mágico, un lugar fantástico donde Harry descubre que no es solo "
            "dos personas, sino muchas. Es un libro sobre la soledad, la identidad y "
            "el aprender a tomarse la vida con un poco de humor."
        ),
        "frase_voz": "Este libro es El lobo estepario, de Hermann Hesse.",
    },
    "ballad_songbirds_en": {
        "titulo": "The Ballad of Songbirds and Snakes",
        "titulo_lcd": "The Ballad of Songbirds and Snakes",
        "autor": "Suzanne Collins",
        "anio": 2020,
        "idioma": "en",
        "idioma_nombre": "English",
        "genero": "distopia",
        "genero_nombre": "Dystopia",
        "color": "#E63946",          # rojo, igual que el LED del tótem
        "color_nombre": "red",
        "emoji": "🐦",
        "resumen": (
            "Sixty-four years before Katniss Everdeen, a young Coriolanus Snow is "
            "eighteen, ambitious, and secretly poor. To win a prize that could save "
            "his family's name, he is chosen to mentor a tribute in the tenth Hunger "
            "Games: Lucy Gray Baird, a bold singer from District 12. As the Games "
            "begin, Snow has to decide how far he is willing to go to win, and what "
            "he is willing to lose. It is a story about power, loyalty and how a "
            "person slowly becomes the villain we already know."
        ),
        "frase_voz": "This book is The Ballad of Songbirds and Snakes, by Suzanne Collins.",
    },
}

# Próxima lectura recomendada según el libro y si le gustó o no.
# Se escriben en el idioma del libro que se reseñó.
RECOMENDACIONES = {
    "lobo_estepario_es": {
        "positivo": {
            "titulo": "Siddhartha",
            "autor": "Hermann Hesse",
            "anio": 1922,
            "por_que": "Si te gustó Harry Haller, Siddhartha es otro viaje interior de Hesse, "
                       "más corto y luminoso, sobre un joven que busca su propio camino.",
        },
        "neutral": {
            "titulo": "El principito",
            "autor": "Antoine de Saint-Exupéry",
            "anio": 1943,
            "por_que": "También habla de la soledad y de lo que de verdad importa, "
                       "pero es corto, sencillo y se lee en una tarde.",
        },
        "negativo": {
            "titulo": "Crónica de una muerte anunciada",
            "autor": "Gabriel García Márquez",
            "anio": 1981,
            "por_que": "Si te pareció lento, esta es corta y llena de suspenso: "
                       "desde la primera página sabes qué va a pasar y quieres saber cómo.",
        },
    },
    "ballad_songbirds_en": {
        "positivo": {
            "titulo": "Sunrise on the Reaping",
            "autor": "Suzanne Collins",
            "anio": 2025,
            "por_que": "Another prequel set in Panem, this time following a young Haymitch "
                       "Abernathy in the fiftieth Hunger Games.",
        },
        "neutral": {
            "titulo": "The Hunger Games",
            "autor": "Suzanne Collins",
            "anio": 2008,
            "por_que": "The original story: faster, with more action, and told by Katniss "
                       "herself. It shows what Snow's choices led to.",
        },
        "negativo": {
            "titulo": "The Giver",
            "autor": "Lois Lowry",
            "anio": 1993,
            "por_que": "A shorter and gentler dystopia about a boy who discovers the secrets "
                       "of his perfect-looking community.",
        },
    },
}

CLASE_SIN_LIBRO = "sin_libro"

# Confianza mínima para aceptar que el modelo reconoció un libro
UMBRAL_CONFIANZA = 0.80


def texto_para_leer(libro):
    """Texto completo que la app lee en voz alta (en el idioma del libro)."""
    return f"{libro['frase_voz']} {libro['resumen']}"


def texto_recomendacion(libro, recomendacion):
    """Frase que la app lee en voz alta al recomendar la próxima lectura."""
    if libro["idioma"] == "en":
        return (
            f"Your next book could be {recomendacion['titulo']}, "
            f"by {recomendacion['autor']}. {recomendacion['por_que']}"
        )
    return (
        f"Te recomiendo leer {recomendacion['titulo']}, "
        f"de {recomendacion['autor']}. {recomendacion['por_que']}"
    )
