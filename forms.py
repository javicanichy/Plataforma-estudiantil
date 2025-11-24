from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, FileField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField, FileAllowed

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
    pie_archivo = StringField('Pie de foto/video', validators=[Length(max=255)])
    destacado = BooleanField('Destacada')
    submit = SubmitField('Publicar')

    class Meta:
        csrf = True
        csrf_strict = False  # permite inputs extra como autor_id



