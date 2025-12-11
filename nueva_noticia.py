# ANTES:
# from servidorBackend import app, db, Usuario, Estudiante, Profesor, Directivo, Administrador

# AHORA (Asumiendo que los modelos están en models.py):
import os
# --- CORRECCIÓN DE IMPORTACIÓN ---
from servidorBackend import app, db 
from models import Usuario, Estudiante, Profesor, Directivo, Administrador
from werkzeug.security import generate_password_hash
# --------------------------------

def create_initial_users():
    """Crea los usuarios de prueba con relaciones 1:1 en la BD local."""
    
    # Contraseña simple para todos los usuarios de prueba
    CLAVE_DEMO = "123456" 
    hashed_password = generate_password_hash(CLAVE_DEMO)
    
    # -------------------------------------------------------------
    # 1. USUARIO ADMINISTRADOR
    # -------------------------------------------------------------
    if not Usuario.query.filter_by(correo="admin@unge.edu").first():
        admin_user = Usuario(
            nombre="Admin",
            apellido="Principal",
            correo="admin@unge.edu",
            password_hash=hashed_password,
            rol="administrador",
        )
        db.session.add(admin_user)
        db.session.commit()
        
        # Crea la entrada de Administrador relacionada (Tabla ADMINISTRADORES)
        admin_data = Administrador(usuario_id=admin_user.id, cargo='Decanato') 
        db.session.add(admin_data)
        print("✅ Administrador creado.")
    else:
        print("⚠️ Administrador ya existe.")
    
    # -------------------------------------------------------------
    # 2. USUARIO PROFESOR
    # -------------------------------------------------------------
    if not Usuario.query.filter_by(correo="profesor@unge.edu").first():
        profesor_user = Usuario(
            nombre="Juan",
            apellido="Perez",
            correo="profesor@unge.edu",
            password_hash=hashed_password,
            rol="profesor",
            curso="Ingeniería", # Columna curso en tabla usuarios
        )
        db.session.add(profesor_user)
        db.session.commit()
        
        # Crea la entrada de Profesor relacionada (Tabla PROFESORES)
        profesor_data = Profesor(usuario_id=profesor_user.id, departamento='Ciencias')
        db.session.add(profesor_data)
        print("✅ Profesor creado.")
    else:
        print("⚠️ Profesor ya existe.")

    # -------------------------------------------------------------
    # 3. USUARIO ESTUDIANTE
    # -------------------------------------------------------------
    if not Usuario.query.filter_by(correo="estudiante@unge.edu").first():
        estudiante_user = Usuario(
            nombre="Ana",
            apellido="García",
            correo="estudiante@unge.edu",
            password_hash=hashed_password,
            rol="estudiante",
            curso="Primero", # Columna curso en tabla usuarios
        )
        db.session.add(estudiante_user)
        db.session.commit()
        
        # Crea la entrada de Estudiante relacionada (Tabla ESTUDIANTES)
        # CORRECCIÓN: Usar 'matricula' en lugar de 'codigo'
        estudiante_data = Estudiante(usuario_id=estudiante_user.id, matricula='E2025001', carrera='Medicina') 
        db.session.add(estudiante_data)
        print("✅ Estudiante creado.")
    else:
        print("⚠️ Estudiante ya existe.")
        
    # -------------------------------------------------------------
    # 4. USUARIO DIRECTIVO
    # -------------------------------------------------------------
    if not Usuario.query.filter_by(correo="directivo@unge.edu").first():
        directivo_user = Usuario(
            nombre="Maria",
            apellido="Lopez",
            correo="directivo@unge.edu",
            password_hash=hashed_password,
            rol="directivo",
        )
        db.session.add(directivo_user)
        db.session.commit()
        
        # Crea la entrada de Directivo relacionada (Tabla DIRECTIVOS)
        directivo_data = Directivo(usuario_id=directivo_user.id, cargo='Jefe de Estudios')
        db.session.add(directivo_data)
        print("✅ Directivo creado.")
    else:
        print("⚠️ Directivo ya existe.")

    db.session.commit()
    print(f"\n¡Proceso de creación de usuarios de prueba completado! Clave: {CLAVE_DEMO}")


if __name__ == "__main__":
    # Esto asegura que el contexto de la aplicación Flask esté activo
    # para que db y los modelos funcionen.
    with app.app_context():
        create_initial_users()