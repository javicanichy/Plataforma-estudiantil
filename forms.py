from random import choice, choices
from flask_wtf import FlaskForm

from wtforms import (
    StringField, TextAreaField, BooleanField, FileField, SubmitField, PasswordField, SelectField
    )

from wtforms.validators import (
    DataRequired, Email, EqualTo, DataRequired, Length, Optional, Length, ValidationError, EqualTo
    )

from flask_wtf.file import FileField, FileAllowed



# ----------------------------------------------------------
# Formulario para crear una noticia
# ----------------------------------------------------------
class NoticiaForm(FlaskForm):
    titulo = StringField('Título', validators=[DataRequired(), Length(max=200)])
    contenido = TextAreaField('Contenido', validators=[DataRequired()])
    archivo = FileField(
        'Imagen o Video (opcional)',
        validators=[
            FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'avi'], 'Solo imágenes o videos válidos')
        ]
    )
    documento = FileField('Documento completo (Word o PDF)', validators=[
        FileAllowed(['docx', 'pdf'], 'Solo archivos Word o PDF')
    ])
    pie_archivo = StringField('Pie de foto/video', validators=[Optional(), Length(max=300)])
    destacado = BooleanField('Destacada')
    submit = SubmitField('Publicar')

    class Meta:
        csrf = True
        csrf_strict = False  # permite inputs extra como autor_id

# ----------------------------------------------------------
# Formulario para editar perfil
# ----------------------------------------------------------
FileAllowed_PERFILES_EXIT = ['jpg', 'jpeg', 'png', 'gif']

class PerfilForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    apellido = StringField('Apellido', validators=[DataRequired(), Length(max=100)])
    curso = StringField('Curso', validators=[Optional(), Length(max=100)])
    biografia = TextAreaField('Biografía', validators=[Optional(), Length(max=500)])
    correo = StringField('Correo electrónico', validators=[DataRequired(), Length(max=150)])
    foto_perfil = FileField('Foto de perfil', validators=[FileAllowed(['jpg','jpeg','png','gif'], 'Solo imágenes')])
    foto_portada = FileField('Foto de portada', validators=[FileAllowed(['jpg','jpeg','png','gif'], 'Solo imágenes')])
    fecha_nacimiento = StringField('Fecha de nacimiento', validators=[DataRequired(), Length(max=20)])
    telefono = StringField('Teléfono', validators=[Optional(), Length(max=20)])
    pais = StringField('País', validators=[DataRequired(), Length(max=100)])
    Residencia = StringField('Residencia', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Actualizar Perfil')


    class Meta:
        csrf = True
        csrf_strict = False


# ----------------------------------------------------------
# Formulario para cambiar contraseña
# ----------------------------------------------------------
class CambiarContrasenaForm(FlaskForm):
    actual = PasswordField('Contraseña actual', validators=[DataRequired()])
    nueva = PasswordField('Nueva contraseña', validators=[DataRequired(), Length(min=6)])
    repetir = PasswordField('Repetir nueva contraseña', validators=[DataRequired(), EqualTo('nueva', message='Las contraseñas deben coincidir')])
    submit = SubmitField('Cambiar Contraseña')


    class Meta:
        csrf = True
        csrf_strict = False  # permite inputs extra como usuario_id


# ----------------------------------------------------------
# Formulario para publicaciones
# ----------------------------------------------------------
class DebateForm(FlaskForm):
    titulo = StringField('Título (obligario)', validators=[DataRequired(message="El titulo es obligatorio"), Length(max=200)])
    contenido = TextAreaField('¿Qué estás pensando?', validators=[DataRequired(), Length(max=1000)])
    archivo = FileField(
        'Adjuntar imagen o video (opcional)',
        validators=[
            FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'avi'], 'Solo imágenes o videos válidos')
        ]
    )
    submit = SubmitField('Publicar')


    class Meta:
        csrf = True
        csrf_strict = False  # permite inputs extra como autor_id


# ----------------------------------------------------------
# Formulario para Biblioteca (PDF o enlace)
# ----------------------------------------------------------
class BibliotecaForm(FlaskForm):
    titulo = StringField('Título', validators=[DataRequired(), Length(max=250)])
    descripcion = TextAreaField('Descripción', validators=[Optional(), Length(max=2000)])
    portada = FileField("Portada", validators=[FileAllowed(['jpg','jpeg','png'], "Solo imágenes")])
    titulacion = SelectField("titulación", validators=[Optional(), Length(max=25)], choices=[
        ("medicina", "Medicina"),
        ("enfermeria grado II", "Enfemeria grado II"),
        ("fisioterapia", "Fisioterapia"),
        ("anestesiologia grado I", "Anestesiologia grado I"),
        ("ginecobstetricia", "Ginecobstetricia"),
        ("laboratorio", "Laboratorio",),
        ("higiene y epidemiologia", "Higiene y Epidemiologia"),
        ("imagenologia", "Imagenologia"),
        ("enfermeria grado I", "Enfermeria grado I")
    ])
    
    # tipo: pdf o link -> SelectField
    tipo = SelectField(
        'Tipo',
        choices=[('pdf', 'PDF'), ('link', 'Enlace externo')],
        validators=[DataRequired()]
    )

    # archivo PDF
    archivo_pdf = FileField(
        'Archivo PDF',
        validators=[FileAllowed(['pdf'], 'Solo se permiten archivos PDF')]
    )

    # enlace alternativo
    enlace = StringField('Enlace externo', validators=[Optional(), Length(max=1000)])

    # tipo_libro: libro o tfg -> SelectField
    tipo_libro = SelectField(
        'Tipo de Material',
        choices=[('libro', 'Libro normal'), ('tfg', 'TFG')],
        validators=[DataRequired()]
    )

    publico = BooleanField('Público')
    submit = SubmitField('Guardar')

    class Meta:
        csrf = True
        csrf_strict = False

# ----------------------------------------------------------
# Formulario para Biblioteca (libro fisico)
# ----------------------------------------------------------
class LibroFisicoForm(FlaskForm):
    titulo = StringField('Título', validators=[DataRequired(), Length(max=250)])
    descripcion = TextAreaField('Descripción', validators=[Optional(), Length(max=2000)])
    portada = FileField("Foto del libro", validators=[FileAllowed(['jpg','jpeg','png'], "Solo imágenes")])
    
    submit = SubmitField("Agregar libro físico")

    class Meta:
        csrf = True
        csrf_strict = False


# ----------------------------------------------------------
# Formulario para prestar libro
# ----------------------------------------------------------
class SolicitudPrestamoForm(FlaskForm):
    motivo = TextAreaField("Motivo del préstamo", validators=[DataRequired()])
    confirmar = BooleanField("Confirmo que deseo solicitar el préstamo y me hago responsable del libro", validators=[DataRequired()])
    submit = SubmitField("Enviar solicitud")