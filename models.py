from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Nullable
from sqlalchemy.sql import func
from datetime import date, datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()


# ============================================================
#   TABLA 1: CÓDIGOS DEL ESTUDIANTE (para registro)
# ============================================================
class CodigoEstudiante(db.Model):
    __tablename__ = 'codigos_estudiantes'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    estudiante_dip = db.Column(db.String(20), nullable=False)
    usado = db.Column(db.Boolean, default=False)
    titulacion_autorizada = db.Column(db.String(100), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Codigo {self.codigo} - Usado: {self.usado}>'


# ============================================================
#   TABLA 2: USUARIOS
# ============================================================
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=True)
    apellidos = db.Column(db.String(100), nullable=True) # Unificado a plural
    sexo = db.Column(db.String(20), nullable=True)
    correo = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='estudiante') # estudiante, profesor, admin
    dip = db.Column(db.String(20), unique=True, nullable=True)
    telefono = db.Column(db.String(20), nullable=True)
    biografia = db.Column(db.Text, nullable=True)
    fecha_nacimiento = db.Column(db.String(20), nullable=True)
    carrera = db.Column(db.String(100), nullable=True)
    curso = db.Column(db.String(100), nullable=True)
    pais = db.Column(db.String(100), nullable=True)
    residencia = db.Column(db.String(100), nullable=True)
    debate = db.Column(db.Integer, default=0) # Para el contador de debates
    notificaciones_activas = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    foto_perfil = db.Column(db.String(255), nullable=True)
    foto_portada = db.Column(db.PickleType, nullable=True) # Mantenemos PickleType como pediste
    correo_institucional = db.Column(db.String(150), unique=True, nullable=True)
    talento = db.Column(db.String(100), nullable=True)
    
    # Relaciones con las demas tablas
    notificaciones = db.relationship("Notificacion", backref="usuario", lazy=True)


    # Relaciones 1 a 1 (Perfiles específicos)
    # uselist=False asegura que un usuario solo tenga un perfil de estudiante o profesor
    estudiante = db.relationship('Estudiante', backref='usuario', uselist=False)
    profesor = db.relationship('Profesor', backref='usuario', uselist=False)
    directivo = db.relationship('Directivo', backref='usuario', uselist=False)
    administrador = db.relationship('Administrador', backref='usuario', uselist=False)

# Método para cifrar la clave al registrarse
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Método para verificar la clave al entrar (Login)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
# ============================================================
#   TABLA 3: ESTUDIANTES
# ============================================================
class Estudiante(db.Model):
    __tablename__ = 'estudiantes'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    matricula = db.Column(db.String(50))
    carrera = db.Column(db.String(100), nullable=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('profesores.id', ondelete='SET NULL'), nullable=True)
    
    # Este es el atajo: permite hacer "estudiante.notas" para ver todos sus expedientes
    notas = db.relationship('Expediente', backref='estudiante', lazy=True)

    def __repr__(self):
        return f"<Estudiante {self.id} {self.matricula}>"


# ============================================================
#   TABLA 4: PROFESORES
# ============================================================
class Profesor(db.Model):
    __tablename__ = 'profesores'
    id = db.Column(db.Integer, primary_key=True)
    
    # El usuario_id debe ser nullable=True porque al inicio NO existe
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    # Campos para guardar los datos del que se registra
    nombre_aspirante = db.Column(db.String(100))
    apellidos_aspirante = db.Column(db.String(100))
    correo_personal = db.Column(db.String(100))
    dip_aspirante = db.Column(db.String(20))
    telefono_aspirante = db.Column(db.String(20))
    sexo_aspirante = db.Column(db.String(20))
    
    # Datos profesionales
    departamento = db.Column(db.String(100))
    especialidad = db.Column(db.String(100))
    archivo_foto = db.Column(db.String(255))
    archivo_dip = db.Column(db.String(255))
    
    # Estado
    cuenta_activa = db.Column(db.Boolean, default=False)
    codigo_activacion = db.Column(db.String(20))

# ============================================================
#   TABLA 5: DIRECTIVOS
# ============================================================
class Directivo(db.Model):
    __tablename__ = 'directivos'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    
    cargo = db.Column(db.String(100), nullable=False)    # Ej: Ilmo. Decano
    facultad = db.Column(db.String(150), nullable=False) # Ej: FICI
    firma_digital = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Directivo {self.cargo}>"


# ============================================================
#   TABLA 6: MENSAJES
# ============================================================
class Mensaje(db.Model):
    __tablename__ = 'mensajes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    emisor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    receptor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    contenido = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, server_default=func.now())
    leido = db.Column(db.Boolean, default=False)
    enviado = db.Column(db.Boolean, default=True)  # true si es enviado, false si es borrador
    recibido = db.Column(db.Boolean, default=True)  # true si está en bandeja de entrada, false si está eliminado
    mensaje_favorito = db.Column(db.Boolean, default=False)
    archivo_adjunto = db.Column(db.String(255), nullable=True)  # ruta al archivo adjunto

    def __repr__(self):
        return f"<Mensaje {self.id}>"
    


# ============================================================
#   TABLA 8: NOTAS
# ============================================================
class Nota(db.Model):
    __tablename__ = 'notas'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    asignatura_id = db.Column(db.Integer, db.ForeignKey('asignaturas.id'), nullable=False)
    
    # 'Práctica', 'Seminario' o 'Evaluación'
    tipo = db.Column(db.String(50), nullable=False) 
    
    # El número de columna (1 al 10)
    posicion = db.Column(db.Integer, nullable=False) 
    
    # Aquí guardamos la calificación o el texto escrito en la celda
    contenido = db.Column(db.String(100), nullable=True) 
    
    # 'like', 'dislike' o None (opcional: puedes ponerlo en Asignatura si es por materia)
    reaccion = db.Column(db.String(20), nullable=True) 
    
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario', backref=db.backref('notas_rel', lazy=True))


# ============================================================
#   TABLA 7: ASIGNATURAS (Se mantiene casi igual)
# ============================================================
class Asignatura(db.Model):
    __tablename__ = 'asignaturas'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    # Nueva columna en lugar de codigo
    creditos = db.Column(db.Integer, default=0) 
    profesor_id = db.Column(db.Integer, db.ForeignKey('profesores.id', ondelete='SET NULL'))

    notas = db.relationship('Nota', backref='asignatura', lazy='dynamic')

# ============================================================
#   TABLA 9: EXPEDIENTES
# ============================================================
class Expediente(db.Model):
    __tablename__ = 'expedientes'
    id = db.Column(db.Integer, primary_key=True)
    
    # Relación con el estudiante
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)
    
    # Datos de la materia
    asignatura_nombre = db.Column(db.String(100), nullable=False)
    nota_final = db.Column(db.Float, nullable=False, default=0.0)
    anio_academico = db.Column(db.String(20), default="2024-2025")
    
    # El sistema de firma
    firmado = db.Column(db.Boolean, default=False)
    fecha_firma = db.Column(db.DateTime, nullable=True) # Para saber cuándo firmó

    def __repr__(self):
        return f'<Nota {self.asignatura_nombre}: {self.nota_final}>'


# ============================================================
#   TABLA 10: EVENTOS
# ============================================================
class Evento(db.Model):
    __tablename__ = 'eventos'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=True)
    all_day = db.Column(db.Boolean, default=False)
    tipo = db.Column(db.String(20), default='general')  # importante, general, divertido
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, server_default=func.now())

    usuario = db.relationship('Usuario', backref='eventos')

    def to_dict(self):
        """Devuelve evento en formato que FullCalendar entiende"""
        return {
            "id": self.id,
            "title": self.titulo,
            "start": self.start.isoformat(),
            "end": self.end.isoformat() if self.end else None,
            "allDay": self.all_day,
            "className": f"evento-{self.tipo}" if self.tipo else "evento-general"
        }

    def __repr__(self):
        return f"<Evento {self.id} {self.titulo}>"


# ============================================================
#   TABLA 11: RELACIÓN ESTUDIANTE ↔ ASIGNATURA (INSCRIPCIONES)
# ============================================================

# ============================================================
#   TABLA 12: ANUNCIOS
# ============================================================
class Anuncio(db.Model):
    __tablename__ = 'anuncios'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(200), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    fecha_publicacion = db.Column(db.DateTime, server_default=func.now())
    autor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)  # relaciona el anuncio con un usuario
    autor = db.relationship('Usuario', backref='anuncios')  # permite acceder al autor desde el anuncio

    def __repr__(self):
        return f"<Anuncio {self.id} {self.titulo}>"
 
# ============================================================
#   TABLA 13: NOTICIAS
# ============================================================
class Noticia(db.Model):
    __tablename__ = 'noticias'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(200), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    archivo = db.Column(db.String(255), nullable=True)  # nombre del archivo (imagen o video)
    tipo_archivo = db.Column(db.String(10), nullable=True)  # 'imagen' o 'video'
    pie_archivo = db.Column(db.String(255), nullable=True)
    enlace_programa = db.Column(db.String(255), nullable=True)
    autor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)  # relaciona la noticia con un usuario
    autor = db.relationship('Usuario', backref='noticias')  # permite acceder al autor desde la noticia
    destacado = db.Column(db.Boolean, default=False)
    documento = db.Column(db.String(255), nullable=True)  # nombre del documento adjunto (PDF u otro)

    def __repr__(self):
        return f"<Noticia {self.id} {self.titulo}>"


# ============================================================
#   TABLA 14: DEBATES
# ============================================================
class Debate(db.Model):
    __tablename__ = 'debates'
    id = db.Column(db.Integer, primary_key=True)
    autor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    fecha_creacion = db.Column(db.DateTime, server_default=func.now())
    archivo = db.Column(db.String(255), nullable=True)
    tipo_archivo = db.Column(db.String(20), nullable=True)

    comentarios = db.relationship('Comentario', backref='debate', cascade='all, delete-orphan')

    
# ============================================================
#   TABLA 15: COMENTARIOS
# ============================================================
class Comentario(db.Model):
    __tablename__ = 'comentarios'
    id = db.Column(db.Integer, primary_key=True)
    debate_id = db.Column(db.Integer, db.ForeignKey('debates.id'), nullable=False)  # <-- rename column
    autor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    fecha_creacion = db.Column(db.DateTime, server_default=func.now())

    autor = db.relationship('Usuario', backref='comentarios')

    def __repr__(self):
        return f"<Comentario {self.id} debate={self.debate_id} autor={self.autor_id}>"

# ============================================================
#   TABLA 16: NOTIFICACIONES
# ============================================================
class Notificacion(db.Model):
    __tablename__ = 'notificaciones'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # 'noticia', 'evento', 'debate'
    referencia_id = db.Column(db.Integer, nullable=True)  # id de noticia, evento o debate
    mensaje = db.Column(db.String(255), nullable=False)
    leida = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, server_default=func.now())

    # 🔗 Relación al usuario
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    
    def __repr__(self):
        return f"<Notificacion {self.id} usuario={self.usuario_id} tipo={self.tipo}>"



# ============================================================
#   TABLA 17: ADMINISTRADOR
# ============================================================
class Administrador(db.Model):
    __tablename__ = "administradores"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), unique=True, nullable=False)
    cargo = db.Column(db.String(100), nullable=True)
    permisos_especiales = db.Column(db.String(200), nullable=True)



# ============================================================
#   TABLA 18: BIBLIOTECA
# ============================================================
class Biblioteca(db.Model):
    __tablename__ = 'biblioteca'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(250), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    tipo = db.Column(db.String(10), nullable=False)  # 'pdf' o 'link'
    archivo = db.Column(db.String(255), nullable=True)  # nombre de archivo en /static/uploads/libros
    enlace = db.Column(db.String(1000), nullable=True)  # si tipo == 'link'
    publico = db.Column(db.Boolean, default=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)  # quien lo subió
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    tipo_libro = db.Column(db.String(10), nullable=False)  # 'libro' o 'tfg' pero en PDF
    portada = db.Column(db.String(300), nullable=True)
    titulacion = db.Column(db.String(20), nullable=True)

    # Relaciones
    uploader = db.relationship('Usuario', backref='biblioteca_items')



# ============================================================
#   TABLA 19: BUZON
# ============================================================
class Buzon(db.Model):
    __tablename__ = 'buzon'
    id = db.Column(db.Integer, primary_key=True)
    tipo_consulta = db.Column(db.String(100), nullable=True) # Ej: "Información académica", "Soporte técnico"
    nombre = db.Column(db.String(100), nullable=True)
    dip = db.Column(db.String(20), nullable=True)
    correo = db.Column(db.String(100), nullable=True)
    mensaje = db.Column(db.Text, nullable=True)
    archivo = db.Column(db.String(255), nullable=True) # Guarda la ruta
    fecha = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================
#   TABLA 20: SELECTIVIDAD
# ============================================================
class Selectividad(db.Model):
    __tablename__ = 'selectividad'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False) # Ej: "Gran fracaso en Biología"
    comentario_admin = db.Column(db.Text, nullable=True) # El comentario que pusimos antes
    ruta_pdf = db.Column(db.String(255), nullable=False)
    ruta_foto = db.Column(db.String(255), nullable=True)
    ruta_pie_foto = db.Column(db.String(255), nullable=True)
    fecha_publicacion = db.Column(db.DateTime, default=datetime.utcnow)
    # Relación para obtener los comentarios de los alumnos
    opiniones = db.relationship('OpinionSelectividad', backref='selectividad', lazy=True)


#============================================================
#   TABLA 21: OPINIONES SELECTIVIDAD
# ============================================================
class OpinionSelectividad(db.Model):
    __tablename__ = 'opiniones_selectividad'
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(100), nullable=False) # Para invitados y logueados
    comentario = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    selectividad_id = db.Column(db.Integer, db.ForeignKey('selectividad.id'), nullable=False)



#============================================================
#   TABLA 22: SOLICITAR LA MATRICULA
# ============================================================
class SolicitudMatricula(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Datos Personales
    tipo_estudiante = db.Column(db.String(50), nullable=False) # Nuevo, Graduado, Continuante
    nombre = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    residencia = db.Column(db.String(200), nullable=False)
    natural_de = db.Column(db.String(100), nullable=False)
    dni_numero = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    carrera = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    sexo = db.Column(db.String(20), nullable=False)
    nacionalidad = db.Column(db.String(100), nullable=False)

    # Archivos Comunes (Para todos)
    doc_dni = db.Column(db.String(255))
    doc_cert_selectividad = db.Column(db.String(255))
    doc_instancia = db.Column(db.String(255))
    doc_hoja_bachillerato = db.Column(db.String(255))
    doc_foto_carnet = db.Column(db.String(255))
    doc_conducta_comunidad = db.Column(db.String(255))
    doc_conducta_centro = db.Column(db.String(255))
    doc_ficha_matricula = db.Column(db.String(255))
    doc_ficha_permanencia = db.Column(db.String(255))

    # Archivos Extra (Graduados / Continuantes / Extranjeros)
    doc_hoja_facultad = db.Column(db.String(255))
    doc_acta_defensa = db.Column(db.String(255))
    doc_convalidaciones = db.Column(db.String(255))
    doc_homologacion = db.Column(db.String(255))

    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='Pendiente')
    observaciones_admin = db.Column(db.Text)