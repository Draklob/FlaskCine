import os
from urllib.parse import urlparse, unquote
from flask import current_app


def validate_url(url):
    print(url)
    if archivo_existe_en_static(url):
        print("Archivo encontrado")
        return True

    print("Comprobando URL")
    try:
        parsed = urlparse(url)
        return all([parsed.scheme, parsed.netloc, parsed.path])
    except:
        return False


def archivo_existe_en_static(ruta_relativa):
    """Verifica si un archivo existe en static/uploads/posters."""
    ruta_absoluta = f"C:/Users/JBP/PycharmProjects/FlaskCine{ruta_relativa}"

    return os.path.isfile(ruta_absoluta)
