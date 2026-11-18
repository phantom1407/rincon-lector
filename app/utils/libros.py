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

CLASE_SIN_LIBRO = "sin_libro"

# Confianza mínima para aceptar que el modelo reconoció un libro
UMBRAL_CONFIANZA = 0.80


def texto_para_leer(libro):
    """Texto completo que la app lee en voz alta (en el idioma del libro)."""
    return f"{libro['frase_voz']} {libro['resumen']}"
