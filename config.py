import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


class Config:
    # Cadena de conexión PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    # Clave secreta de la app (sesiones y cookies)
    SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(24))

    # Carpeta para subir archivos
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "static/uploads")

    # Limite máximo de subida (2MB)
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024

    # Optimización de SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False