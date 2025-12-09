from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from datetime import date, datetime


db = SQLAlchemy()


# ============================================================
#   TABLA 0: PRE-MATRÍCULA (antes de tener cuenta)
# ============================================================
class Matricula(db.Model):
    __tablename__ = 'matriculas'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), nullable=False, unique=True)
    carrera = db.Column(db.String(100), nullable=False)
    fecha_solicitud = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Matricula {self.id} {self.nombre} {self.carrera}>"


# ============================================================
#   TABLA 1: CÓDIGOS DEL ESTUDIANTE (para registro)
# ============================================================
class CodigoEstudiante(db.Model):
    __tablename__ = 'codigos_estudiante'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False, index=True)
    correo = db.Column(db.String(100), nullable=False)
    usado = db.Column(db.Boolean, default=False, nullable=False)
    fecha_creacion = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<CodigoEstudiante {self.codigo} {self.correo} usado={self.usado}>"


# ============================================================
#   TABLA 2: USUARIOS
# ============================================================
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=True)
    correo = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False)  # estudiante, profesor, directivo, administrador
    fecha_creacion = db.Column(db.DateTime, server_default=func.now())
    foto_perfil = db.Column(db.String(255), nullable=True)  # ruta a la foto de perfil
    curso = db.Column(db.String(100), nullable=True)
    fecha_nacimiento = db.Column(db.String(20), nullable=True)
    foto_portada = db.Column(db.PickleType, nullable=True)
    telefono = db.Column(db.String(20), nullable=True)
    biografia = db.Column(db.Text, nullable=True)
    pais = db.Column(db.String(100), nullable=True)
    residencia = db.Column(db.String(100), nullable=True)
    notificaciones_activas = db.Column(db.Boolean, default=True)  # recibir notificaciones por correo

    # Relación con las notificaciones
    notificaciones = db.relationship("Notificacion", backref="usuario", lazy=True)

    # Relaciones 1 a 1
    estudiante = db.relationship('Estudiante', backref='usuario', uselist=False)
    profesor = db.relationship('Profesor', backref='usuario', uselist=False)
    directivo = db.relationship('Directivo', backref='usuario', uselist=False)
    administrador = db.relationship('Administrador', backref='usuario', uselist=False)

    # Relaciones mensajes
    mensajes_enviados = db.relationship(
        'Mensaje',
        foreign_keys='Mensaje.emisor_id',
        backref='emisor',
        lazy='dynamic'
    )
    mensajes_recibidos = db.relationship(
        'Mensaje',
        foreign_keys='Mensaje.receptor_id',
        backref='receptor',
        lazy='dynamic'
    )

    def __repr__(self):
        return f"<Usuario {self.id} {self.correo}>"


# ============================================================
#   TABLA 3: ESTUDIANTES
# ============================================================
class Estudiante(db.Model):
    __tablename__ = 'estudiantes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    matricula = db.Column(db.String(50), unique=True, nullable=False)
    carrera = db.Column(db.String(100), nullable=False)
    semestre = db.Column(db.Integer, nullable=True)
    grupo = db.Column(db.String(20), nullable=True)
    estado_academico = db.Column(db.String(20), default="activo")  # activo, retirado, graduado
    tutor_id = db.Column(db.Integer, db.ForeignKey('profesores.id', ondelete='SET NULL'))
    fecha_ingreso = db.Column(db.DateTime, server_default=func.now())

    # notas
    notas = db.relationship('Nota', backref='estudiante', lazy='dynamic')

    # expedientes
    expedientes = db.relationship('Expediente', backref='estudiante', lazy='dynamic')

    def __repr__(self):
        return f"<Estudiante {self.id} {self.matricula}>"


# ============================================================
#   TABLA 4: PROFESORES
# ============================================================
class Profesor(db.Model):
    __tablename__ = 'profesores'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    departamento = db.Column(db.String(100), nullable=False)
    fecha_ingreso = db.Column(db.DateTime, server_default=func.now())

    # asignaturas
    asignaturas = db.relationship('Asignatura', backref='profesor', lazy='dynamic')

    # tutorías
    tutorados = db.relationship('Estudiante', backref='tutor', lazy='dynamic')

    def __repr__(self):
        return f"<Profesor {self.id}>"


# ============================================================
#   TABLA 5: DIRECTIVOS
# ============================================================
class Directivo(db.Model):
    __tablename__ = 'directivos'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    cargo = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Directivo {self.id}>"


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
#   TABLA 7: ASIGNATURAS
# ============================================================
class Asignatura(db.Model):
    __tablename__ = 'asignaturas'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(50), unique=True, nullable=False, index=True)
    profesor_id = db.Column(db.Integer, db.ForeignKey('profesores.id', ondelete='SET NULL'))

    # notas
    notas = db.relationship('Nota', backref='asignatura', lazy='dynamic')

    def __repr__(self):
        return f"<Asignatura {self.codigo}>"


# ============================================================
#   TABLA 8: NOTAS
# ============================================================
class Nota(db.Model):
    __tablename__ = 'notas'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id', ondelete='CASCADE'), nullable=False)
    asignatura_id = db.Column(db.Integer, db.ForeignKey('asignaturas.id', ondelete='CASCADE'), nullable=False)
    nota = db.Column(db.Float, nullable=False)
    fecha_registro = db.Column(db.DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Nota {self.id} {self.nota}>"


# ============================================================
#   TABLA 9: EXPEDIENTES
# ============================================================
class Expediente(db.Model):
    __tablename__ = 'expedientes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id', ondelete='CASCADE'), nullable=False)
    nombre_documento = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(50), nullable=True)  # pdf, imagen, certificado...
    ruta_archivo = db.Column(db.Text, nullable=False)
    fecha_subida = db.Column(db.DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Expediente {self.id}>"


# ============================================================
#   TABLA 10: CALENDARIO
# ============================================================
class Calendario(db.Model):
    __tablename__ = 'calendario'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time)
    creado_por = db.Column(db.String(255))
    fecha_creacion = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f'<Calendario {self.titulo} - {self.fecha}>'


# ============================================================
#   TABLA 11: RELACIÓN ESTUDIANTE ↔ ASIGNATURA (INSCRIPCIONES)
# ============================================================
class EstudianteAsignatura(db.Model):
    __tablename__ = 'estudiante_asignatura'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id', ondelete='CASCADE'), nullable=False)
    asignatura_id = db.Column(db.Integer, db.ForeignKey('asignaturas.id', ondelete='CASCADE'), nullable=False)
    fecha_inscripcion = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<EstudianteAsignatura estudiante={self.estudiante_id} asignatura={self.asignatura_id}>"


# ============================================================
#   TABLA 12: EVENTOS
# ============================================================
class Evento(db.Model):
    __tablename__ = 'eventos'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fecha = db.Column(db.String(20), nullable=False)   # yyyy-mm-dd
    hora = db.Column(db.String(10), nullable=False)    # hh:mm
    descripcion = db.Column(db.String(255), nullable=False)
    creador_id = db.Column(db.Integer, nullable=False)  # id del usuario que creó el evento
    fecha_creacion = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'fecha': self.fecha,
            'hora': self.hora,
            'descripcion': self.descripcion,
            'creador_id': self.creador_id
        }

    def __repr__(self):
        return f"<Evento {self.fecha} {self.hora} {self.descripcion}>"
    

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