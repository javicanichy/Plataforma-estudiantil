from servidorBackend import app, db, Usuario
from werkzeug.security import generate_password_hash

with app.app_context():
    # Correos de prueba
    correos_prueba = ["isaias@example.com", "maria@example.com", "juan@example.com"]
    
    # Borrar usuarios existentes con estos correos
    Usuario.query.filter(Usuario.correo.in_(correos_prueba)).delete(synchronize_session=False)
    db.session.commit()

    # Crear nuevos usuarios de prueba
    usuarios = [
        {"nombre": "Isaias", "apellido": "Nkogo", "correo": "isaias@example.com", "clave": "1234", "rol": "estudiante"},
        {"nombre": "Maria", "apellido": "Perez", "correo": "maria@example.com", "clave": "abcd", "rol": "profesor"},
        {"nombre": "Juan", "apellido": "Gomez", "correo": "juan@example.com", "clave": "pass123", "rol": "directivo"},
    ]

    for u in usuarios:
        nuevo_usuario = Usuario(
            nombre=u["nombre"],
            apellido=u["apellido"],
            correo=u["correo"].lower(),
            password_hash=generate_password_hash(u["clave"]),
            rol=u["rol"]
        )
        db.session.add(nuevo_usuario)

    db.session.commit()
    print("Usuarios de prueba creados correctamente.")
