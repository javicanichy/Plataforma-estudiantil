import os

class Config:
    # Cadena de conexión PostgreSQL
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:javi1234@localhost:5432/Base_de_datos_para_FCS"
    
    # Desactivar el seguimiento de modificaciones de SQLAlchemy (mejora rendimiento)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Clave secreta de la app (para sesiones y cookies)
    # En producción es recomendable establecer una fija desde variables de entorno
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24))