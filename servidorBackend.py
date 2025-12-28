import os
import re

from dotenv import load_dotenv
from datetime import datetime, date
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix
from email_validator import validate_email, EmailNotValidError
from io import BytesIO
from docx import Document
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fpdf import FPDF

from flask import (
    Flask, jsonify, request, redirect, url_for, send_file, send_from_directory,
    render_template, send_file, session, abort, flash, Blueprint, current_app, make_response
)

import unicodedata
import logging
import smtplib
import io
import bleach
import uuid
import email_validator
import secrets
import string
import random
import pandas as pd

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_cors import CORS
from flask_mail import Message, Mail, Connection
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, FileField, SubmitField


from forms import (
    NoticiaForm, PerfilForm, CambiarContrasenaForm, FileAllowed_PERFILES_EXIT, Email, EqualTo, DataRequired, 
    Length, Optional, ValidationError, PasswordField, DebateForm, BibliotecaForm, LibroFisicoForm,
    SolicitudPrestamoForm, BuzonAyudaForm, OpinionForm, SelectividadForm, SelectividadForm, MatriculaForm
    )

from models import (
    db, Usuario, Estudiante, Nota, Mensaje, Evento, Evento, Debate, Notificacion, Administrador, Comentario,
    CodigoEstudiante, Asignatura, Noticia, Debate, Notificacion, Comentario,
    Biblioteca, Buzon, OpinionSelectividad, Selectividad, SolicitudMatricula, Expediente, Profesor,
    Directivo
    )
    
from config import Config
from flask_migrate import Migrate



"""=========================================
 ESTRUCTURA BÁSICA:
 1. Base de datos → PostgreSQL
 2. Backend → Flask + SQLAlchemy + CORS
 3. Frontend → HTML + CSS + JS (Fetch API)
 ========================================="""



# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================

# Cargar variables de entorno
load_dotenv()

# Directorios
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Configurar app de Flask
app = Flask(__name__, static_folder=STATIC_DIR, template_folder=TEMPLATES_DIR)
# APLICAR PROXY FIX: Corrige la gestión de sesiones bajo el proxy de Render (HTTPS)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Configuarar db
# db = SQLAlchemy()

# Configuracion desde config.py
app.config.from_object(Config)

# SEGURIDAD Y SESIONES
#-----------------------------------------
app.secret_key = app.config['SECRET_KEY']

# Permite hasta 32 Megabytes de subida (suficiente para todos los PDFs y fotos)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

# Indica a Flask que confíe en los proxies (necesario en Render/servidores en la nube)
app.config['PREFERRED_URL_SCHEME'] = 'https'
#Forzar que la cookie de sesión solo se envíe sobre HTTPS, esto resuelve el problema de la sesión en el navegador de Render
app.config['SESSION_COOKIE_SECURE'] = True

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
#-----------------------------------------

# MANEJAR CORREOS ELECTRONICOS. BUZON DE AYUDA
app.config['MAIL_SERVER'] = 'smtp.gmail.com'        # servidor SMTP, puedes cambiarlo según tu correo
app.config['MAIL_PORT'] = 587                       # puerto TLS
app.config['MAIL_USE_TLS'] = True                   # usar TLS
app.config['MAIL_USE_SSL'] = False                  # no usar SSL porque usamos TLS
app.config['MAIL_USERNAME'] = 'tucorreo@gmail.com'  # tu correo
app.config['MAIL_PASSWORD'] = 'tu_contraseña_app'   # contraseña de aplicación o normal (Gmail necesita app password)
app.config['MAIL_DEFAULT_SENDER'] = 'tucorreo@gmail.com'  # remitente por defecto

# Inicializar Flask-Mail
mail = Mail(app)



# SEGUNDA CONFIGURACION DEL CORREO. SECRETARIA-MATRICULA, ESTUDIANTES
# Definimos estas variables por separado para no sobrescribir app.config
"""CORREO_MATRICULAS_USER = 'secretaria-matriculas@gmail.com' 
CORREO_MATRICULAS_PASS = 'tu_segunda_contraseña_app'
CORREO_MATRICULAS_SERVER = 'smtp.gmail.com'
CORREO_MATRICULAS_PORT = 587"""


# TERCERA CONFIGURACION DEL CORREO. REGISTRO DE PROFESORES
# Definimos estas variables por separado para no sobrescribir app.config
"""CORREO_MATRICULAS_USER = 'secretaria-matriculas@gmail.com' 
CORREO_MATRICULAS_PASS = 'tu_segunda_contraseña_app'
CORREO_MATRICULAS_SERVER = 'smtp.gmail.com'
CORREO_MATRICULAS_PORT = 587"""


# CONFIGURACIÓN DE CORREO (TEMPORAL PARA MAILHOG).
# ==========================================
CORREO_MATRICULAS_SERVER = 'localhost'
CORREO_MATRICULAS_PORT = 1025
CORREO_MATRICULAS_USER = 'test@unge.gq'
CORREO_MATRICULAS_PASS = '' 
# ==========================================

# Arancar la abse de datos
db.init_app(app)
CORS(app)

# Mirgraciones
migrate = Migrate(app, db)





# Definición del Blueprint
eventos_bp = Blueprint('eventos', __name__, url_prefix='/api/eventos')


# ===== INYECTAR VARIABLES GLOBALES EN TODOS LOS TEMPLATES (ANTES DE CUALQUIER RUTA) =====
@app.context_processor
def inyectar_contexto():
    """Inyecta datos del usuario en TODOS los templates automáticamente"""
    return {
        'logueado': current_user.is_authenticated,
        'usuario': current_user.nombre if current_user.is_authenticated else 'Invitado',
        'rol': current_user.rol if current_user.is_authenticated else None,
        'usuario_id': current_user.id if current_user.is_authenticated else None,
        'current_user': current_user  # Esto te permite usar {{ current_user.apellidos }} en cualquier HTML
    }

# ==========================================================
# MANEJO DE ARCHIVOS
# ==========================================================

# Carpeta donde se guardarán los archivos subidos
UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_IMAGE_EXT = {'jpg', 'jpeg', 'png', 'gif'}
ALLOWED_VIDEO_EXT = {'mp4', 'mov', 'avi'}
ALLOWED_EXT = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT



# Carpeta base para todos los archivos subidos
UPLOADS_DIR = os.path.join(STATIC_DIR, 'uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)  # Crear uploads si no existe

def guardar_archivo(archivo, categoria):
    """
    Guarda un archivo subido en la carpeta correcta según categoría.
    Devuelve la ruta relativa para guardar en DB.
    """
    if not archivo:
        return None

    # Crear carpeta de categoría si no existe
    carpeta_destino = os.path.join(UPLOADS_DIR, categoria)
    os.makedirs(carpeta_destino, exist_ok=True)

    # Nombre seguro
    filename = secure_filename(archivo.filename)

    # Ruta final en el sistema
    ruta_guardado = os.path.join(carpeta_destino, filename)
    archivo.save(ruta_guardado)

    # Ruta relativa para templates / URLs
    return f'uploads/{categoria}/{filename}'



# ==========================================================
# DECORADORES PROFESIONALES. Rol restrintion
# ==========================================================


# 1. Decorador para verificar si está logueado
def requiere_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # En lugar de buscar en 'session', preguntamos a Flask-Login
        if not current_user.is_authenticated:
            flash("Por favor, inicia sesión para acceder.", "warning")
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# 2. Decorador para verificar el ROL
def requiere_rol(rol_permitido):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verificamos si está logueado Y si su rol coincide
            if not current_user.is_authenticated or current_user.rol != rol_permitido:
                flash(f"Acceso denegado. Se requiere rol de {rol_permitido}.", "danger")
                return redirect(url_for('inicio'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
# ===========================================================================
# CONFIGURACIÓN DE CARRERAS Y CURSOS (Diccionario)
CARRERAS_INFO = {
    'Grado Medicina': {'años': 6},
    'Grado II Enfermería': {'años': 4},
    'Grado Fisioterapia': {'años': 4},
    'Grado I Enfermería': {'años': 3},
    'Grado I Ginecobstetrica': {'años': 3},
    'Grado I Laboratorio': {'años': 3},
    'Grado I Epidemiologia': {'años': 3},
    'Grado I Imagenologia': {'años': 3},
    'Grado I Anestesiologia': {'años': 3}
}


# ==========================================================
# RUTAS PÚBLICAS
# ==========================================================
@app.route('/', methods=['GET', 'POST'])
def inicio():
    form = BuzonAyudaForm()
    
    if form.validate_on_submit():
        tipo = form.tipo_consulta.data  # 'matricula' o 'general'
        ruta_archivo = None
        
        # 1. Guardar el archivo PDF si existe
        if form.archivo.data:
            ruta_completa = guardar_archivo(form.archivo.data, 'matriculas_docs')
            # Extraemos solo el nombre: "Seleccion_Masculina_FCS.pdf"
            nombre_solo = os.path.basename(ruta_completa)
            ruta_archivo = nombre_solo

        try:
            # 2. PROCESO EXCLUSIVO PARA MATRÍCULA/ADMISIÓN
            if tipo == 'matricula':
                dip_ingresado = form.dip.data
                # Buscamos al estudiante en la tabla de solicitudes
                estudiante = SolicitudMatricula.query.filter_by(dni_numero=dip_ingresado).first()
                
                if estudiante:
                    # Vinculamos el documento directamente a su ficha de matrícula
                    if ruta_archivo:
                        estudiante.doc_ficha_matricula = ruta_archivo
                        estudiante.estado = "Pendiente" # Marcamos para revisión del admin
                    
                    # Creamos el registro en el buzón con referencia al alumno
                    nueva_consulta = Buzon(
                        tipo_consulta='matricula',
                        nombre=f"{estudiante.nombre} {estudiante.apellidos}",
                        dip=dip_ingresado,
                        correo=form.correo.data,
                        mensaje=f"[TRÁMITE ADMISIÓN] {form.mensaje.data}",
                        archivo=ruta_archivo
                    )
                    flash(f"Documento vinculado al DIP {dip_ingresado} correctamente.", "success")
                else:
                    # Si el DIP no existe, el admin lo recibirá como alerta de DIP no encontrado
                    nueva_consulta = Buzon(
                        tipo_consulta='matricula',
                        nombre="DIP NO REGISTRADO",
                        dip=dip_ingresado,
                        correo=form.correo.data,
                        mensaje=f"ALERTA: Intento de envío con DIP inexistente: {form.mensaje.data}",
                        archivo=ruta_archivo
                    )
                    flash("El DIP no coincide, pero su mensaje fue enviado al administrador.", "warning")

            # 3. PROCESO PARA CONSULTA GENERAL
            else:
                nueva_consulta = Buzon(
                    tipo_consulta='general',
                    nombre=form.nombre.data,
                    correo=form.correo.data,
                    mensaje=form.mensaje.data,
                    archivo=ruta_archivo
                )
                flash("Consulta general enviada con éxito.", "success")

            db.session.add(nueva_consulta)
            db.session.commit()
            return redirect(url_for('inicio', _anchor='buzon'))

        except Exception as e:
            db.session.rollback()
            print(f"Error en el proceso: {e}")
            flash("Error al procesar la solicitud.", "danger")
            
    return render_template('index.html', form=form, noticias=Noticia.query.all())

@app.route('/ver-documento/<filename>')
def ver_documento(filename):
    folder = os.path.join(app.root_path, 'static', 'uploads', 'matriculas_docs')
    
    # Comprobamos si el archivo existe físicamente
    if not os.path.exists(os.path.join(folder, filename)):
        return "Archivo no encontrado", 404

    response = make_response(send_from_directory(folder, filename))
    
    # Estos encabezados son los que convencen a Chrome de mostrarlo
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline'
    # Esta línea elimina restricciones de seguridad para el visor
    response.headers['X-Frame-Options'] = 'ALLOWALL' 
    
    return response

@app.route('/admin/buzon-general')
# @login_required  <-- Descomenta esto si usas LoginManager
def buzon_general():
    # Filtramos solo las que son de tipo 'general'
    consultas = Buzon.query.filter_by(tipo_consulta='general').order_by(Buzon.fecha.desc()).all()
    return render_template('buzon.html', consultas=consultas)

@app.route('/login')
def login_page():
    return render_template('login.html', body_class="fondo-login")

@app.route('/registro', methods=['GET', 'POST'])
def registro_page():
    return render_template('registro.html')

@app.route("/noticias")
def noticias_page():
    noticias = Noticia.query.order_by(Noticia.fecha.desc()).all()
    return render_template("lista_noticia.html", noticias=noticias)

@app.route('/contacto')
def contacto_page():
    return render_template('contacto.html')


@app.route('/requisitos')
def requisitos():
    return render_template('requisitos.html')

@app.route('/asignaturas')
def asignaturas_page():
    return render_template('asignaturas.html')

@app.route('/calendario')
def calendario_page():
    return render_template('calendario.html', body_class="calendario-page")

@app.route('/mensajes')
def mensajes_page():
    return render_template('mensajes.html')

@app.route('/perfil')
def perfil_page():
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión", "warning")
        return redirect(url_for('login_page'))
    return redirect(url_for('ver_perfil', usuario_id=session['usuario_id']))



# ==========================================================
# Inject current_user into templates
@app.context_processor
def inject_user():
    if 'usuario_id' in session:
        usuario = Usuario.query.get(session['usuario_id'])
        return {'current_user': usuario}
    return {'current_user': None}

@app.route("/biblioteca")
def biblioteca_page():
    # Libros de TFG visibles para todos
    filtro_titulacion = request.args.get("titulacion", None)

    query_tfg = Biblioteca.query.filter_by(tipo_libro="tfg", publico=True)

    if filtro_titulacion and filtro_titulacion != "":
        query_tfg = query_tfg.filter_by(titulacion=filtro_titulacion)

    tfg_publicos = query_tfg.order_by(Biblioteca.titulacion.asc(), Biblioteca.fecha_creacion.desc()).all()

    return render_template(
        "biblioteca.html",
        tfg_publicos=tfg_publicos,
        filtro_titulacion=filtro_titulacion,
        body_class="biblioteca-page"
    )

# ==========================================================
# API: SESIÓN DE USUARIO
# ==========================================================
@app.route('/api/login', methods=['POST'])
@app.route('/login', methods=['POST'])
def api_login():
    if not request.is_json:
        return jsonify({'mensaje': 'Se requiere JSON'}), 400

    data = request.get_json()
    # Ahora solo aceptamos el correo institucional
    correo_inst = (data.get('correo') or data.get('email') or '').strip().lower()
    clave = data.get('clave') or data.get('password') or ''

    # Buscamos EXCLUSIVAMENTE en la columna de correo institucional
    usuario = Usuario.query.filter_by(correo_institucional=correo_inst).first()

    if not usuario:
        return jsonify({
            'ok': False, 
            'mensaje': 'Correo institucional no registrado o incorrecto'
        }), 404

    # Verificación de la contraseña creada en el registro/wizard
    if not check_password_hash(usuario.password_hash, clave):
        return jsonify({'ok': False, 'mensaje': 'Contraseña incorrecta'}), 401

    # Flask-Login gestiona la sesión
    login_user(usuario, remember=True) 

    # Sincronización de sesión manual (opcional, por compatibilidad)
    session['usuario_id'] = usuario.id
    session['nombre'] = usuario.nombre
    session['rol'] = usuario.rol

    return jsonify({
        'ok': True,
        'mensaje': 'Acceso concedido',
        'usuario': {
            'id': usuario.id, 
            'nombre': usuario.nombre, 
            'correo': usuario.correo_institucional,
            'talento': usuario.talento
        }
    }), 200


@app.route('/api/usuario_sesion', methods=['GET'])
def usuario_sesion():
    # Ahora usamos current_user de Flask-Login (mucho más seguro)
    from flask_login import current_user
    
    if not current_user.is_authenticated:
        return jsonify({'logueado': False})
        
    return jsonify({
        'logueado': True,
        'id': current_user.id,
        'nombre': current_user.nombre,
        'rol': current_user.rol,
        'talento': getattr(current_user, 'talento', None) # Ya incluimos el talento
    })



# ==========================================================
# API: CREACION DE CORREOS CORPORATIVOS PARA ESTUDIANTES
# ==========================================================
def crear_correo_unge_estandar(nombre, apellidos):
    """
    Genera correo: inicialesNombre.primerApellido.año.cienciasdelasalud@unge.gq
    Ejemplo: Isaias Nkogo + Esono Aviri -> in.esono.2025.cienciasdelasalud@unge.gq
    """
    def normalizar(texto):
        if not texto: return ""
        # Elimina acentos y convierte a minúsculas
        texto_norm = unicodedata.normalize('NFD', texto)
        return "".join(c for c in texto_norm if unicodedata.category(c) != 'Mn').lower().strip()

    # 1. Obtener iniciales de TODOS los nombres (Isaias Nkogo -> in)
    nombres_lista = nombre.split()
    iniciales = "".join([normalizar(n)[0] for n in nombres_lista if n])

    # 2. Obtener solo el primer apellido (Esono Aviri -> esono)
    primer_apellido = normalizar(apellidos.split()[0])

    # 3. Año actual
    anio = str(datetime.now().year)

    # 4. Construir base con el estándar fijo de la facultad
    # Resultado: in.esono.2025.cienciasdelasalud
    correo_base = f"{iniciales}.{primer_apellido}.{anio}.cienciasdelasalud"
    dominio = "@unge.gq"
    
    email_final = f"{correo_base}{dominio}"
    
    # 5. Control de duplicados (en caso de que dos alumnos tengan mismas iniciales y apellido)
    contador = 1
    while Usuario.query.filter_by(correo_institucional=email_final).first():
        email_final = f"{correo_base}{contador}{dominio}"
        contador += 1
        
    return email_final



def enviar_codigo_activacion(solicitud, codigo_nuevo, dominio):
    """
    Envía el correo de aprobación con el código de un solo uso,
    manteniendo el diseño institucional de la UNGE.
    """
    email_destino = solicitud.email
    nombre_alumno = f"{solicitud.nombre} {solicitud.apellidos}"
    carrera_alumno = solicitud.carrera

    msg = MIMEMultipart('alternative')
    msg['From'] = f"Secretaría Académica UNGE <{CORREO_MATRICULAS_USER}>"
    msg['To'] = email_destino
    msg['Subject'] = "¡Solicitud Admitida! - Código de Activación de Cuenta"

    # Enlace directo al wizard de registro
    url_registro = f"{dominio}/registro-estudiante"

    html_content = f"""
    <html>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7f9;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse; background-color: #ffffff; margin-top: 30px; border-radius: 15px; border: 1px solid #e1e8ed; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            
            <tr>
                <td align="center" style="padding: 40px 0 20px 0; background-color: #ffffff;">
                    <img src="{dominio}/static/img/logo_unge.jpeg" alt="Logo UNGE" width="100" style="display: block; margin-bottom: 15px;">
                    <h1 style="margin: 0; font-size: 14px; color: #1a237e; letter-spacing: 1px; text-transform: uppercase;">Universidad Nacional de Guinea Ecuatorial</h1>
                    <p style="margin: 5px 0 0 0; font-size: 16px; color: #ff6f00; font-weight: bold;">Facultad de Ciencias de la Salud</p>
                </td>
            </tr>

            <tr>
                <td style="padding: 20px 40px; text-align: center; background-color: #1b5e20;">
                    <h2 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: 300; letter-spacing: 1px;">SOLICITUD ADMITIDA</h2>
                </td>
            </tr>

            <tr>
                <td style="padding: 40px 40px 20px 40px;">
                    <p style="font-size: 18px; color: #2c3e50; margin-bottom: 25px;">¡Felicidades, <strong>{nombre_alumno}</strong>!</p>
                    
                    <p style="font-size: 15px; color: #546e7a; line-height: 1.6; margin-bottom: 25px;">
                        Nos complace informarle que su solicitud para la carrera de <strong>{carrera_alumno}</strong> ha sido <strong>APROBADA</strong>. 
                        Ya puede proceder a activar su cuenta de estudiante y generar su correo institucional.
                    </p>

                    <div style="background-color: #f1f8e9; border-radius: 10px; padding: 25px; border: 2px dashed #1b5e20; text-align: center; margin-bottom: 30px;">
                        <p style="margin: 0 0 10px 0; font-size: 13px; color: #1b5e20; font-weight: bold; text-transform: uppercase;">Su código de activación es:</p>
                        <span style="font-size: 32px; font-weight: bold; color: #1b5e20; letter-spacing: 4px;">{codigo_nuevo}</span>
                    </div>

                    <p style="font-size: 15px; color: #455a64; margin-bottom: 25px; text-align: center;">
                        Para activar su cuenta, haga clic en el siguiente botón e introduzca su DIP junto con este código:
                    </p>

                    <div style="text-align: center; margin-bottom: 30px;">
                        <a href="{url_registro}" style="background-color: #1a237e; color: #ffffff; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px; display: inline-block;">ACTIVAR MI CUENTA</a>
                    </div>

                    <p style="font-size: 13px; color: #78909c; text-align: center; font-style: italic;">
                        Recuerde que este código es de un solo uso y es personal e intransferible.
                    </p>
                </td>
            </tr>

            <tr>
                <td style="background-color: #eceff1; padding: 30px; text-align: center; border-top: 1px solid #cfd8dc;">
                    <p style="margin: 0; color: #78909c; font-size: 12px; line-height: 1.5;">
                        <strong>Secretaría Académica - Facultad de Ciencias de la Salud</strong><br>
                        Campus de Bata, Guinea Ecuatorial<br>
                        Este es un mensaje automático, por favor no responda a este correo.
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP(CORREO_MATRICULAS_SERVER, CORREO_MATRICULAS_PORT)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error al enviar código de activación: {e}")
        return False


# NO ENVIAR CODIGO DE ESTUDIANTE SI COMPROBANTE DE MATRICULA NO ESTÁ APROBADO
def enviar_rechazo_solicitud(solicitud, motivo, dominio):
    """
    Envía el correo de rechazo o solicitud de corrección,
    manteniendo la línea gráfica de la UNGE.
    """
    email_destino = solicitud.email
    nombre_alumno = f"{solicitud.nombre} {solicitud.apellidos}"
    carrera_alumno = solicitud.carrera

    msg = MIMEMultipart('alternative')
    msg['From'] = f"Secretaría Académica UNGE <{CORREO_MATRICULAS_USER}>"
    msg['To'] = email_destino
    msg['Subject'] = "Acción Requerida: Revisión de su Solicitud de Matrícula"

    html_content = f"""
    <html>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7f9;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse; background-color: #ffffff; margin-top: 30px; border-radius: 15px; border: 1px solid #e1e8ed; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            
            <tr>
                <td align="center" style="padding: 40px 0 20px 0; background-color: #ffffff;">
                    <img src="{dominio}/static/img/logo_unge.jpeg" alt="Logo UNGE" width="100" style="display: block; margin-bottom: 15px;">
                    <h1 style="margin: 0; font-size: 14px; color: #1a237e; letter-spacing: 1px; text-transform: uppercase;">Universidad Nacional de Guinea Ecuatorial</h1>
                    <p style="margin: 5px 0 0 0; font-size: 16px; color: #ff6f00; font-weight: bold;">Facultad de Ciencias de la Salud</p>
                </td>
            </tr>

            <tr>
                <td style="padding: 20px 40px; text-align: center; background-color: #b71c1c;">
                    <h2 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: 300; letter-spacing: 1px;">SOLICITUD RECHAZADA / PENDIENTE</h2>
                </td>
            </tr>

            <tr>
                <td style="padding: 40px 40px 20px 40px;">
                    <p style="font-size: 18px; color: #2c3e50; margin-bottom: 25px;">Estimado/a <strong>{nombre_alumno}</strong>,</p>
                    
                    <p style="font-size: 15px; color: #546e7a; line-height: 1.6; margin-bottom: 25px;">
                        Lamentamos informarle que su solicitud para la carrera de <strong>{carrera_alumno}</strong> no ha podido ser procesada debido a inconsistencias en la documentación presentada.
                    </p>

                    <div style="background-color: #fff8e1; border-radius: 10px; padding: 25px; border-left: 5px solid #ff6f00; margin-bottom: 30px;">
                        <p style="margin: 0 0 10px 0; font-size: 13px; color: #e65100; font-weight: bold; text-transform: uppercase;">Observaciones de Secretaría:</p>
                        <p style="font-size: 16px; color: #333; font-style: italic; margin: 0;">"{motivo}"</p>
                    </div>

                    <p style="font-size: 15px; color: #455a64; margin-bottom: 25px;">
                        Para continuar con su proceso de inscripción, es necesario que subsane los errores mencionados. Por favor, póngase en contacto con la administración o realice una nueva solicitud con los documentos correctos.
                    </p>

                    <p style="font-size: 13px; color: #78909c; text-align: center; font-style: italic;">
                        Su expediente permanecerá en estado de pausa hasta que se reciba la corrección requerida.
                    </p>
                </td>
            </tr>

            <tr>
                <td style="background-color: #eceff1; padding: 30px; text-align: center; border-top: 1px solid #cfd8dc;">
                    <p style="margin: 0; color: #78909c; font-size: 12px; line-height: 1.5;">
                        <strong>Secretaría Académica - Facultad de Ciencias de la Salud</strong><br>
                        Campus de Bata, Guinea Ecuatorial<br>
                        Este es un mensaje automático, por favor no responda a este correo.
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP(CORREO_MATRICULAS_SERVER, CORREO_MATRICULAS_PORT)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error al enviar correo de rechazo: {e}")
        return False


# ==========================================================
# API: REGISTRO PARA ESTUDIANTES
# ==========================================================
@app.route('/registro-estudiante', methods=['GET', 'POST'])
def registro_estudiante():
    if current_user.is_authenticated:
        return redirect(url_for('inicio'))

    if request.method == 'POST':
        datos = request.form
        dip_ingresado = datos.get('dip')
        codigo_ingresado = datos.get('codigo_estudiante')

        # 1. Validar Código de Estudiante
        codigo_db = CodigoEstudiante.query.filter_by(
            codigo=codigo_ingresado, 
            estudiante_dip=dip_ingresado,
            usado=False
        ).first()

        if not codigo_db:
            return render_template('registro_fallido.html', mensaje="El código o el DIP no son válidos o ya han sido usados.")

        # 2. Buscar la Solicitud de Matrícula
        solicitud = SolicitudMatricula.query.filter_by(dni_numero=dip_ingresado).first()

        if not solicitud:
            return render_template('registro_fallido.html', mensaje="No se encontró una solicitud de matrícula aprobada para este DIP.")

        # 3. Lógica de creación de correo institucional
        email_inst = crear_correo_unge_estandar(solicitud.nombre, solicitud.apellidos)

        try:
            # 4. Crear el Usuario con TRASPASO AUTOMÁTICO
            nuevo_usuario = Usuario(
                nombre=solicitud.nombre,
                apellidos=solicitud.apellidos,
                sexo=solicitud.sexo, 
                correo=solicitud.email, 
                correo_institucional=email_inst,
                dip=solicitud.dni_numero,
                telefono=solicitud.telefono,
                fecha_nacimiento=str(solicitud.fecha_nacimiento),
                residencia=solicitud.residencia,
                pais=solicitud.nacionalidad,
                carrera=codigo_db.titulacion_autorizada,
                # --- NUEVOS CAMPOS ---
                talento=datos.get('talento'), # Recogemos el valor del select con iconos
                biografia=datos.get('biografia'),
                rol='estudiante'
            )
            # El método set_password se encarga de que el correo institucional 
            # reconozca la clave mediante el hash de seguridad.
            nuevo_usuario.set_password(datos.get('password'))

            # Marcar código como usado
            codigo_db.usado = True
            
            db.session.add(nuevo_usuario)
            db.session.commit()

            # Inicio de sesión automático tras activar
            login_user(nuevo_usuario)
            
            # Pasamos el usuario al template para mostrar su nuevo correo institucional
            return render_template('registro_exitoso.html', usuario=nuevo_usuario)

        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}") # Para depuración en consola
            return render_template('registro_fallido.html', mensaje=f"Error al procesar el registro: {str(e)}")

    return render_template('registro_wizard.html')


# Mostrar el nombre y apellido asociado a un DIP
@app.route('/verificar-dip/<dip>')
def verificar_dip(dip):
    solicitud = SolicitudMatricula.query.filter_by(dni_numero=dip).first()
    if solicitud:
        return jsonify({
            'encontrado': True,
            'nombre': solicitud.nombre,
            'apellido': solicitud.apellidos
        })
    return jsonify({'encontrado': False})

# PROCESAR SOLICITUD DE CODIGO DE MATRICULA, LO QUE VE EL ADMIN
@app.route('/admin/panel-solicitudes')
def panel_admin_solicitudes():
    # FILTRO DEFINITIVO: Solo mostramos los que tienen estado 'Admitido'
    # Así cumplimos tu regla de que primero debe ser admitido en revisión de expediente
    solicitudes = SolicitudMatricula.query.filter_by(estado='Admitido').all()
    
    # Obtenemos los datos del buzón para saber el "Tipo de Matrícula"
    # Usamos el DNI/DIP como llave de cruce
    mensajes_buzon = {b.dip: b for b in Buzon.query.all()}
    codigos = {c.estudiante_dip: c for c in CodigoEstudiante.query.all()}

    return render_template('admin_solicitudes.html', 
                           solicitudes=solicitudes, 
                           mensajes_buzon=mensajes_buzon, 
                           codigos=codigos)

# PERMITIR AUTOGENERACION DE CODIGO ESTUDIANTE POR PARTE DE ADMINISTRADOR
# Reutilizamos tu instancia de mail configurada con Mailhog
def generar_codigo_seguro():
    caracteres = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(8))

@app.route('/admin/aprobar-solicitud/<int:id>')
def aprobar_solicitud(id):
    solicitud = SolicitudMatricula.query.get_or_404(id)
    
    # 1. Generar código
    codigo_txt = f"UNGE-{generar_codigo_seguro()}"
    dominio_actual = request.host_url.rstrip('/') 

    nuevo_permiso = CodigoEstudiante(
        codigo=codigo_txt,
        estudiante_dip=solicitud.dni_numero,
        titulacion_autorizada=solicitud.carrera,
        usado=False
    )
    
    try:
        db.session.add(nuevo_permiso)
        
        # 2. ENVIAR EL NUEVO CORREO ESTRUCTURADO
        envio_exitoso = enviar_codigo_activacion(solicitud, codigo_txt, dominio_actual)
        
        if envio_exitoso:
            db.session.commit()
            return jsonify({"status": "success", "codigo": codigo_txt})
        else:
            return jsonify({"status": "error", "message": "Error al conectar con Mailhog"})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)})

# NO ENVIAR CODIGO DE ESTUDIANTE SI COMPROBANTE DE MATRICULA NO ESTÁ APROBADO
@app.route('/admin/rechazar-solicitud/<int:id>', methods=['POST'])
def rechazar_solicitud(id):
    solicitud = SolicitudMatricula.query.get_or_404(id)
    datos = request.get_json()
    motivo_txt = datos.get('motivo', 'Documentación incompleta o ilegible.')
    
    dominio_actual = request.host_url.rstrip('/')

    try:
        # Enviamos el correo con el nuevo diseño institucional de rechazo
        envio_ok = enviar_rechazo_solicitud(solicitud, motivo_txt, dominio_actual)
        
        if envio_ok:
            solicitud.estado = "Rechazada"
            # Opcional: podrías guardar el motivo en la BD si tienes esa columna
            # solicitud.observaciones_admin = motivo_txt
            db.session.commit()
            return jsonify({"status": "success", "message": "Estudiante notificado correctamente"})
        else:
            return jsonify({"status": "error", "message": "No se pudo conectar con el servidor de correo"})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================================
# INSCRIPCIÓN DE ASIGNATURAS
# ==========================================================
@app.route('/api/inscribir', methods=['POST'])
@requiere_rol('estudiante')
def api_inscribir_asignatura():
    data = request.get_json()
    asignatura_id = data.get('asignatura_id')

    estudiante = Estudiante.query.filter_by(usuario_id=session['usuario_id']).first()
    if not estudiante:
        return jsonify({'ok': False, 'msg': 'Estudiante no encontrado'}), 404

    existe = EstudianteAsignatura.query.filter_by(
        estudiante_id=estudiante.id,
        asignatura_id=asignatura_id
    ).first()
    if existe:
        return jsonify({'ok': False, 'msg': 'Ya inscrito'}), 400

    inscripcion = EstudianteAsignatura()
    inscripcion.estudiante_id = estudiante.id
    inscripcion.asignatura_id = asignatura_id
    db.session.add(inscripcion)
    db.session.commit()

    return jsonify({'ok': True, 'msg': 'Inscripción exitosa'})


# ==========================================================
# CERRAR SESION
# ==========================================================

from flask import make_response

@app.route('/logout')
@login_required
def logout():
    # 1. Avisar a Flask-Login que cierre la sesión
    logout_user()
    
    # 2. Limpiar todos los datos de la sesión de Flask
    session.clear()
    
    # 3. Crear la respuesta de redirección
    response = make_response(redirect(url_for('login_page')))
    
    # 4. BORRADO MANUAL DE COOKIES
    # Flask suele usar 'session' o 'remember_token'
    response.delete_cookie('session')
    response.delete_cookie('remember_token')
    
    # 5. Forzar al navegador a no usar caché (para que refresque el menú)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    flash("Has salido del sistema.", "info")
    return response


# ==========================================================
# API: MENSAJERÍA (Mensajes)
# ==========================================================
@app.route('/api/mensajes', methods=['POST'])
def api_enviar_mensaje():
    """
    Enviar mensaje:
    Espera JSON: { "receptor_id": int, "contenido": "texto" }
    Necesita sesión iniciada (session['usuario_id'])
    """
    if 'usuario_id' not in session:
        return jsonify({'ok': False, 'msg': 'No autenticado'}), 401

    if not request.is_json:
        return jsonify({'ok': False, 'msg': 'Se requiere JSON'}), 400

    data = request.get_json()
    receptor_id = data.get('receptor_id')
    contenido = (data.get('contenido') or '').strip()

    if not receptor_id or not contenido:
        return jsonify({'ok': False, 'msg': 'Faltan campos'}), 400

    try:
        # Verificar que exista el receptor (opcional, pero útil)
        receptor = Usuario.query.get(receptor_id)
        if not receptor:
            return jsonify({'ok': False, 'msg': 'Receptor no encontrado'}), 404

        emisor_id = session['usuario_id']
        nuevo = Mensaje()
        nuevo.emisor_id = emisor_id
        nuevo.receptor_id = receptor_id
        nuevo.contenido = contenido
        db.session.add(nuevo)
        db.session.commit()

        return jsonify({
            'ok': True,
            'msg': 'Mensaje enviado',
            'mensaje': {
                'id': nuevo.id,
                'emisor_id': nuevo.emisor_id,
                'receptor_id': nuevo.receptor_id,
                'contenido': nuevo.contenido,
                'fecha': nuevo.fecha.isoformat() if nuevo.fecha else None,
                'leido': bool(nuevo.leido)
            }
        }), 201
    except Exception as e:
        print(f'Error al enviar mensaje: {e}')
        db.session.rollback()
        return jsonify({'ok': False, 'msg': 'Error al enviar mensaje'}), 500


@app.route('/api/mensajes/<int:usuario_id>', methods=['GET'])
def api_mensajes_usuario(usuario_id):
    """
    Obtener todos los mensajes relacionados con un usuario:
    Devuelve mensajes donde usuario_id sea emisor o receptor, ordenados por fecha asc.
    Si el request es de un usuario autenticado distinto, se puede permitir la lectura
    sólo si es el mismo usuario (aquí permitimos sólo si está autenticado y coincide).
    """
    if 'usuario_id' not in session:
        return jsonify({'ok': False, 'msg': 'No autenticado'}), 401

    # Solo el propio usuario (o un rol admin) puede listar sus mensajes
    if session['usuario_id'] != usuario_id and session.get('rol') != 'admin':
        return jsonify({'ok': False, 'msg': 'Permisos insuficientes'}), 403

    try:
        mensajes = Mensaje.query.filter(
            (Mensaje.emisor_id == usuario_id) | (Mensaje.receptor_id == usuario_id)
        ).order_by(Mensaje.fecha.asc()).all()

        result = []
        for m in mensajes:
            # intento incluir nombre de emisor/receptor si existe
            emisor = Usuario.query.get(m.emisor_id) if m.emisor_id else None
            receptor = Usuario.query.get(m.receptor_id) if m.receptor_id else None
            result.append({
                'id': m.id,
                'emisor_id': m.emisor_id,
                'emisor_nombre': emisor.nombre if emisor else None,
                'receptor_id': m.receptor_id,
                'receptor_nombre': receptor.nombre if receptor else None,
                'contenido': m.contenido,
                'fecha': m.fecha.isoformat() if m.fecha else None,
                'leido': bool(m.leido)
            })

        return jsonify({'ok': True, 'mensajes': result})
    except Exception as e:
        print(f'Error al listar mensajes usuario {usuario_id}: {e}')
        return jsonify({'ok': False, 'msg': 'Error al cargar mensajes'}), 500


@app.route('/api/conversacion/<int:user1>/<int:user2>', methods=['GET'])
def api_conversacion(user1, user2):
    """
    Obtener conversación entre user1 y user2 (tanto emisor->receptor como receptor->emisor),
    ordenada por fecha asc.
    Acceso: cualquiera de los dos usuarios (o admin).
    """
    if 'usuario_id' not in session:
        return jsonify({'ok': False, 'msg': 'No autenticado'}), 401

    current = session['usuario_id']
    if current not in (user1, user2) and session.get('rol') != 'admin':
        return jsonify({'ok': False, 'msg': 'Permisos insuficientes'}), 403

    try:
        conv = Mensaje.query.filter(
            ((Mensaje.emisor_id == user1) & (Mensaje.receptor_id == user2)) |
            ((Mensaje.emisor_id == user2) & (Mensaje.receptor_id == user1))
        ).order_by(Mensaje.fecha.asc()).all()

        result = []
        for m in conv:
            result.append({
                'id': m.id,
                'emisor_id': m.emisor_id,
                'receptor_id': m.receptor_id,
                'contenido': m.contenido,
                'fecha': m.fecha.isoformat() if m.fecha else None,
                'leido': bool(m.leido)
            })
        return jsonify({'ok': True, 'conversacion': result})
    except Exception as e:
        print(f'Error al cargar conversacion {user1}-{user2}: {e}')
        return jsonify({'ok': False, 'msg': 'Error al cargar conversación'}), 500


@app.route('/api/mensajes/<int:msg_id>/leer', methods=['POST'])
def api_marcar_leido(msg_id):
    """
    Marcar un mensaje como leído. Sólo el receptor puede marcarlo.
    """
    if 'usuario_id' not in session:
        return jsonify({'ok': False, 'msg': 'No autenticado'}), 401

    try:
        m = Mensaje.query.get(msg_id)
        if not m:
            return jsonify({'ok': False, 'msg': 'Mensaje no encontrado'}), 404

        if m.receptor_id != session['usuario_id']:
            return jsonify({'ok': False, 'msg': 'No eres el receptor'}), 403

        m.leido = True
        db.session.commit()
        return jsonify({'ok': True, 'msg': 'Mensaje marcado como leído'})
    except Exception as e:
        print(f'Error al marcar leido mensaje {msg_id}: {e}')
        db.session.rollback()
        return jsonify({'ok': False, 'msg': 'Error al actualizar mensaje'}), 500


# Listar mensajes agrupados por usuario (conversaciones)
@app.route('/api/mis-chats/<int:usuario_id>', methods=['GET'])
def api_mis_chats(usuario_id):
    """
    Lista de personas con las que el usuario ha hablado.
    Devuelve 1 registro por usuario (sin duplicados),
    con su último mensaje y fecha.
    """
    if 'usuario_id' not in session:
        return jsonify({'ok': False, 'msg': 'No autenticado'}), 401

    # Solo el dueño de la cuenta o admin
    if session['usuario_id'] != usuario_id and session.get('rol') != 'admin':
        return jsonify({'ok': False, 'msg': 'Permisos insuficientes'}), 403

    try:
        # Buscar mensajes donde el usuario sea emisor O receptor
        mensajes = Mensaje.query.filter(
            (Mensaje.emisor_id == usuario_id) | (Mensaje.receptor_id == usuario_id)
        ).order_by(Mensaje.fecha.desc()).all()

        chats = {}
        for m in mensajes:
            otro_id = m.receptor_id if m.emisor_id == usuario_id else m.emisor_id

            if not otro_id:
                continue

            # Solo guardar el primer mensaje encontrado (el más reciente)
            if otro_id not in chats:
                otro_user = Usuario.query.get(otro_id)
                chats[otro_id] = {
                    'usuario_id': otro_id,
                    'nombre': otro_user.nombre if otro_user else 'Usuario desconocido',
                    'ultimo_mensaje': m.contenido,
                    'fecha': m.fecha.isoformat() if m.fecha else None
                }

        return jsonify({'ok': True, 'chats': list(chats.values())})

    except Exception as e:
        print(f'Error al obtener lista de chats de {usuario_id}: {e}')
        return jsonify({'ok': False, 'msg': 'Error interno'}), 500

# Eliminar mensajes (el emisor puede eliminar sus mensajes, tambien se elimina para el receptor)
@app.route('/api/mensajes/<int:msg_id>', methods=['DELETE'])
def api_eliminar_mensaje(msg_id):
    """
    Eliminar un mensaje por su ID.
    Sólo el emisor puede eliminar su mensaje.
    """
    if 'usuario_id' not in session:
        return jsonify({'ok': False, 'msg': 'No autenticado'}), 401

    try:
        m = Mensaje.query.get(msg_id)
        if not m:
            return jsonify({'ok': False, 'msg': 'Mensaje no encontrado'}), 404

        if m.emisor_id != session['usuario_id']:
            return jsonify({'ok': False, 'msg': 'No eres el emisor'}), 403

        db.session.delete(m)
        db.session.commit()
        return jsonify({'ok': True, 'msg': 'Mensaje eliminado'})
    except Exception as e:
        print(f'Error al eliminar mensaje {msg_id}: {e}')
        db.session.rollback()
        return jsonify({'ok': False, 'msg': 'Error al eliminar mensaje'}), 500

# Editar mensaje enviado
@app.route('/api/mensajes/<int:msg_id>', methods=['PUT'])
def api_editar_mensaje(msg_id):
    """
    Editar el contenido de un mensaje enviado.
    Sólo el emisor puede editar su mensaje.
    Espera JSON: { "contenido": "nuevo texto" }
    """
    if 'usuario_id' not in session:
        return jsonify({'ok': False, 'msg': 'No autenticado'}), 401

    if not request.is_json:
        return jsonify({'ok': False, 'msg': 'Se requiere JSON'}), 400

    data = request.get_json()
    nuevo_contenido = (data.get('contenido') or '').strip()

    if not nuevo_contenido:
        return jsonify({'ok': False, 'msg': 'Contenido vacío'}), 400

    try:
        m = Mensaje.query.get(msg_id)
        if not m:
            return jsonify({'ok': False, 'msg': 'Mensaje no encontrado'}), 404

        if m.emisor_id != session['usuario_id']:
            return jsonify({'ok': False, 'msg': 'No eres el emisor'}), 403

        m.contenido = nuevo_contenido
        db.session.commit()
        return jsonify({'ok': True, 'msg': 'Mensaje editado'})
    except Exception as e:
        print(f'Error al editar mensaje {msg_id}: {e}')
        db.session.rollback()
        return jsonify({'ok': False, 'msg': 'Error al editar mensaje'}), 500
    
# Contador de mensajes no leídos
@app.route('/api/mensajes/no-leidos', methods=['GET'])
def api_mensajes_no_leidos():
    """
    Devuelve el número de mensajes no leídos para el usuario autenticado.
    """
    if 'usuario_id' not in session:
        return jsonify({'ok': False, 'msg': 'No autenticado'}), 401

    try:
        count = Mensaje.query.filter_by(
            receptor_id=session['usuario_id'],
            leido=False
        ).count()
        return jsonify({'ok': True, 'no_leidos': count})
    except Exception as e:
        print(f'Error al contar mensajes no leídos: {e}')
        return jsonify({'ok': False, 'msg': 'Error interno'}), 500

# Guardar mensajes como favoritos
@app.route('/api/mensajes/<int:msg_id>/favorito', methods=['POST'])
def api_favorito_mensaje(msg_id):
    """
    Marcar o desmarcar un mensaje como favorito.
    Espera JSON: { "favorito": true/false }
    Sólo el receptor puede marcar favoritos.
    """
    if 'usuario_id' not in session:
        return jsonify({'ok': False, 'msg': 'No autenticado'}), 401

    if not request.is_json:
        return jsonify({'ok': False, 'msg': 'Se requiere JSON'}), 400

    data = request.get_json()
    es_favorito = data.get('favorito', False)

    try:
        m = Mensaje.query.get(msg_id)
        if not m:
            return jsonify({'ok': False, 'msg': 'Mensaje no encontrado'}), 404

        if m.receptor_id != session['usuario_id']:
            return jsonify({'ok': False, 'msg': 'No eres el receptor'}), 403

        m.favorito = bool(es_favorito)
        db.session.commit()
        return jsonify({'ok': True, 'msg': 'Mensaje actualizado como favorito'})
    except Exception as e:
        print(f'Error al actualizar favorito mensaje {msg_id}: {e}')
        db.session.rollback()
        return jsonify({'ok': False, 'msg': 'Error al actualizar mensaje'}), 500
    
# Guardar mensajes como favoritos
@app.route('/api/mensajes/favoritos', methods=['GET'])
def api_listar_mensajes_favoritos():
    """
    Listar todos los mensajes marcados como favoritos para el usuario autenticado.
    """
    if 'usuario_id' not in session:
        return jsonify({'ok': False, 'msg': 'No autenticado'}), 401

    try:
        mensajes = Mensaje.query.filter_by(
            receptor_id=session['usuario_id'],
            favorito=True
        ).order_by(Mensaje.fecha.desc()).all()

        result = []
        for m in mensajes:
            result.append({
                'id': m.id,
                'emisor_id': m.emisor_id,
                'receptor_id': m.receptor_id,
                'contenido': m.contenido,
                'fecha': m.fecha.isoformat() if m.fecha else None,
                'leido': bool(m.leido)
            })
        return jsonify({'ok': True, 'mensajes_favoritos': result})
    except Exception as e:
        print(f'Error al listar mensajes favoritos: {e}')
        return jsonify({'ok': False, 'msg': 'Error interno'}), 500
    
# cada vez que el receptor ve el mensaje se actualiza
@app.route('/api/mensajes/<int:msg_id>/visto', methods=['POST'])
def api_marcar_visto_mensaje(msg_id):
    """
    Marcar un mensaje como visto. Sólo el receptor puede marcarlo.
    """
    if 'usuario_id' not in session:
        return jsonify({'ok': False, 'msg': 'No autenticado'}), 401

    try:
        m = Mensaje.query.get(msg_id)
        if not m:
            return jsonify({'ok': False, 'msg': 'Mensaje no encontrado'}), 404

        if m.receptor_id != session['usuario_id']:
            return jsonify({'ok': False, 'msg': 'No eres el receptor'}), 403

        m.visto = True
        db.session.commit()
        return jsonify({'ok': True, 'msg': 'Mensaje marcado como visto'})
    except Exception as e:
        print(f'Error al marcar visto mensaje {msg_id}: {e}')
        db.session.rollback()
        return jsonify({'ok': False, 'msg': 'Error al actualizar mensaje'}), 500
    
# Adjuntar archivos a mensajes (opcional)
@app.route('/api/mensajes/<int:msg_id>/adjuntar', methods=['POST'])
def api_adjuntar_archivo_mensaje(msg_id):
    """
    Adjuntar un archivo a un mensaje existente.
    Sólo el emisor puede adjuntar archivos a su mensaje.
    Espera un archivo en form-data con clave 'archivo'.
    """
    if 'usuario_id' not in session:
        return jsonify({'ok': False, 'msg': 'No autenticado'}), 401

    archivo = request.files.get('archivo')
    if not archivo or not archivo.filename:
        return jsonify({'ok': False, 'msg': 'No se proporcionó archivo'}), 400

    if not allowed_file(archivo.filename):
        return jsonify({'ok': False, 'msg': 'Tipo de archivo no permitido'}), 400

    try:
        m = Mensaje.query.get(msg_id)
        if not m:
            return jsonify({'ok': False, 'msg': 'Mensaje no encontrado'}), 404

        if m.emisor_id != session['usuario_id']:
            return jsonify({'ok': False, 'msg': 'No eres el emisor'}), 403

        filename = secure_filename(archivo.filename)
        dest = os.path.join(UPLOADS_DIR, filename)
        # evitar sobreescritura
        if os.path.exists(dest):
            import time
            filename = f"{int(time.time())}_{filename}"
            dest = os.path.join(UPLOADS_DIR, filename)
        archivo.save(dest)

        m.archivo_adjunto = filename
        db.session.commit()
        return jsonify({'ok': True, 'msg': 'Archivo adjuntado al mensaje', 'archivo': filename})
    except Exception as e:
        print(f'Error al adjuntar archivo mensaje {msg_id}: {e}')
        db.session.rollback()
        return jsonify({'ok': False, 'msg': 'Error al adjuntar archivo'}), 500



# ==========================================================
# API CALENDARIO
# ==========================================================
@eventos_bp.route('/', methods=['GET'])
@requiere_login
def get_eventos():
    eventos = Evento.query.all()
    return jsonify([e.to_dict() for e in eventos])

@eventos_bp.route('/', methods=['POST'])
@requiere_login
@requiere_rol('directivo')
def crear_evento():
    data = request.get_json()
    titulo = data.get('title')
    descripcion = data.get('descripcion')
    start = data.get('start')
    end = data.get('end')
    all_day = data.get('allDay', False)
    tipo = data.get('tipo', 'general')

    if not titulo or not start:
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
    end_dt = datetime.fromisoformat(end.replace('Z', '+00:00')) if end else None

    evento = Evento(
        titulo=titulo,
        descripcion=descripcion,
        start=start_dt,
        end=end_dt,
        all_day=all_day,
        tipo=tipo,
        usuario_id=session.get('usuario_id')
    )
    db.session.add(evento)
    db.session.commit()
    return jsonify(evento.to_dict()), 201

@eventos_bp.route('/<int:evento_id>', methods=['DELETE'])
@requiere_login
@requiere_rol('directivo')
def eliminar_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    db.session.delete(evento)
    db.session.commit()
    return jsonify({"mensaje": "Evento eliminado"}), 200

# Registrar Blueprint después de definir todas las rutas
app.register_blueprint(eventos_bp)


# ==========================
# RUTA PERFIL
# ==========================

# Guardar imagen de perfil
def save_profile_image(foto):
    ext = foto.filename.rsplit('.', 1)[-1].lower()
    if ext not in FileAllowed_PERFILES_EXIT:
        return None
    nombre_archivo = f"{uuid.uuid4().hex}_{secure_filename(foto.filename)}"
    carpeta = os.path.join(app.static_folder, 'uploads', 'perfiles')
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre_archivo)
    foto.save(ruta)
    return nombre_archivo

# Guardar imagen de portada
def save_cover_image(foto):
    ext = foto.filename.rsplit('.', 1)[-1].lower()
    if ext not in FileAllowed_PERFILES_EXIT:
        return None
    nombre_archivo = f"{uuid.uuid4().hex}_{secure_filename(foto.filename)}"
    carpeta = os.path.join(app.static_folder, 'uploads', 'portadas')
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre_archivo)
    foto.save(ruta)
    return nombre_archivo


# Ver perfil
@app.route('/perfil/<int:usuario_id>')
def ver_perfil(usuario_id):
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        flash("Usuario no encontrado", "danger")
        return redirect(url_for('inicio'))

    # Limitar a las 5 noticias más recientes
    if usuario.noticias:
        usuario.noticias_ultimas = sorted(usuario.noticias, key=lambda x: x.fecha, reverse=True)[:5]
    else:
        usuario.noticias_ultimas = []

    return render_template('perfil.html', usuario=usuario)

# EDITAR PERFIL
@app.route('/perfil/editar', methods=['GET', 'POST'])
def perfil_editar():
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión", "warning")
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['usuario_id'])

    if request.method == 'POST':
        usuario.nombre = request.form.get('nombre')
        usuario.correo = request.form.get('correo')

        # Si quieres agregar foto de perfil
        foto = request.files.get('foto_perfil')
        if foto:
            filename_perfil = save_profile_image(foto) # filename es lavariabke que guardamos, pero con su apoto
            if filename_perfil:
                usuario.foto_perfil = filename_perfil

        # Para agregar foto de portada
        foto_portada = request.files.getlist('foto_portada')
        lista_fotos = []
        for una_foto in foto_portada[:3]: # Maximo de 3 fotos
            filename_portada = save_cover_image(una_foto) # Para que el servidor reciba una sola foto
            if filename_portada:
                lista_fotos.append(filename_portada)
        if lista_fotos:
            usuario.foto_portada = lista_fotos

        db.session.commit()
        flash("Perfil actualizado", "success")
        return redirect(url_for('ver_perfil', usuario_id=usuario.id))

    return render_template('perfil_editar.html', usuario=usuario)

# CAMBIAR CONTRASEÑA
@app.route('/perfil/cambiar_contrasena', methods=['GET', 'POST'])
def perfil_cambiar_contrasena():
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión", "warning")
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['usuario_id'])

    if request.method == 'POST':
        actual = request.form.get('actual')
        nueva = request.form.get('nueva')
        confirmar = request.form.get('confirmar')

        if not check_password_hash(usuario.contrasena, actual):
            flash("Contraseña actual incorrecta", "danger")
            return redirect(url_for('perfil_cambiar_contrasena'))

        if nueva != confirmar:
            flash("La nueva contraseña no coincide", "danger")
            return redirect(url_for('perfil_cambiar_contrasena'))

        usuario.contrasena = generate_password_hash(nueva)
        db.session.commit()
        flash("Contraseña cambiada con éxito", "success")
        return redirect(url_for('ver_perfil', usuario_id=usuario.id))

    return render_template('perfil_cambiar_contrasena.html')

# DEBATES
@app.route('/crear_debate', methods=['GET', 'POST'])
@requiere_login
def crear_debate():
    form = DebateForm()
    if form.validate_on_submit():
        archivo_nombre = None
        tipo_archivo = None

        # Guardar archivo si existe
        if form.archivo.data:
            archivo_nombre = secure_filename(form.archivo.data.filename)
            form.archivo.data.save(os.path.join(UPLOAD_FOLDER, archivo_nombre))
            ext = archivo_nombre.rsplit('.',1)[1].lower()
            tipo_archivo = 'video' if ext=='mp4' else 'imagen'

        # Crear el debate
        publicacion = Debate(
            titulo=form.titulo.data,
            contenido=form.contenido.data,
            archivo=archivo_nombre,
            tipo_archivo=tipo_archivo,
            autor_id=session['usuario_id'],
            fecha_creacion=func.now()  # usa la fecha actual
        )

        db.session.add(publicacion)
        db.session.commit()

        # Crear notificaciones para todos los usuarios excepto el creador
        usuario = Usuario.query.get(session['usuario_id'])
        todos_usuarios = Usuario.query.filter(Usuario.id != usuario.id).all()

        for otro_usuario in todos_usuarios:
            notificacion = Notificacion(
                usuario_id=otro_usuario.id,
                tipo='debate',
                mensaje=f"{usuario.nombre} creó un nuevo debate: {publicacion.titulo}"
            )
            db.session.add(notificacion)

        db.session.commit()

        flash('Debate creado correctamente y notificación enviada a todos los miembros', 'success')
        return redirect(url_for('perfil_debates'))

    return render_template('crear_debate.html', form=form)



# RUTAS DEL PERFIL
@app.route('/configuracion')
def configuracion():
    return render_template('configuracion.html')

@app.route('/estudios')
def estudios():
    return render_template('estudios.html')

@app.route('/facultad')
def facultad():
    return render_template('facultad.html')



# ==========================
# NOTICIAS
# ==========================
# Lista de etiquetas permitidas
tags_permitidas = ['p','b','i','u','ul','li','a','img','strong','em','br','h1','h2','h3']

# Atributos permitidos
atributos_permitidos = {
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
}




@app.route('/nueva_noticia', methods=['GET', 'POST'])
@requiere_login  # Proteger la ruta si no hay sesion
def nueva_noticia():
    form = NoticiaForm()
    autor_id = session.get('usuario_id')

    if form.validate_on_submit():
        # Obtener el ID del usuario desde la sesión
        autor_id = session.get('usuario_id')
        
        if not autor_id:
            flash("Error: no se pudo identificar al autor de la noticia.", "danger")
            return redirect(url_for("nueva_noticia"))
        
        # Manejar archivo Word/PDF
        archivo = form.archivo.data
        nombre_archivo = None
        tipo_archivo = None

        # Guardar archivo si se ha subido
        if archivo:
            nombre_archivo = secure_filename(archivo.filename)
            archivo.save(os.path.join(UPLOAD_FOLDER, nombre_archivo))

            ext = nombre_archivo.rsplit('.', 1)[1].lower()

            if ext in ALLOWED_IMAGE_EXT:
                tipo_archivo = 'imagen'
            elif ext in ALLOWED_VIDEO_EXT:
                tipo_archivo = 'video'
            else:
                flash('Formato de archivo no permitido', 'danger')
                return redirect(url_for('nueva_noticia'))
            
        # Guardar documento Word o PDF
        documento = form.documento.data
        nombre_documento = None
        if documento:
            nombre_documento = secure_filename(documento.filename)
            documento.save(os.path.join(UPLOAD_FOLDER, nombre_documento))

        

                # Crear noticia con autor_id
        noticia = Noticia(
            titulo=form.titulo.data,
            contenido=form.contenido.data,
            fecha=date.today(),
            archivo=nombre_archivo,
            tipo_archivo=tipo_archivo,
            destacado=form.destacado.data,
            documento=nombre_documento,  # <-- aquí guardamos el Word/PDF
            autor_id=autor_id,   # Aquí guardamos el autor desde la sesión
            pie_archivo=form.pie_archivo.data
        )

        db.session.add(noticia)
        db.session.commit()

        flash('Noticia publicada correctamente', 'success')
        return redirect(url_for('noticia_completa', noticia_id=noticia.id))

    return render_template('nueva_noticia.html', form=form, autor_id=autor_id)

# Noticia completa
@app.route('/noticias/<int:noticia_id>')
def noticia_completa(noticia_id):
    noticia = Noticia.query.get_or_404(noticia_id)
    return render_template('noticia_completa.html', noticia=noticia)


# Lista de todas las noticias
@app.route('/lista_noticias')
def lista_noticias():
    noticias = Noticia.query.order_by(Noticia.fecha.desc()).all()
    return render_template('lista_noticias.html', noticias=noticias)


# Eliminar noticia
@app.route('/eliminar_noticia/<int:noticia_id>', methods=['POST'])
@requiere_login
def eliminar_noticia(noticia_id):
    noticia = Noticia.query.get_or_404(noticia_id)
    usuario_actual_id = session.get('usuario_id')
    
    if noticia.autor_id != usuario_actual_id:
        flash("No tienes permisos para eliminar esta noticia.", "danger")
        return redirect(url_for('noticias_page'))

    db.session.delete(noticia)
    db.session.commit()
    flash("Noticia eliminada correctamente.", "success")
    return redirect(url_for('ver_perfil'))

# Descargar documento asociado a noticia
@app.route('/descargar_noticia/<int:noticia_id>')
@requiere_login
def descargar_noticia(noticia_id):
    noticia = Noticia.query.get_or_404(noticia_id)
    if not noticia.documento:
        flash('No hay documento disponible', 'warning')
        return redirect(url_for('noticias_page'))

    return send_file(
        os.path.join(UPLOAD_FOLDER, noticia.documento),
        as_attachment=True
    )

#Ordenar noticas por fecha descendente.Mostrar solo hasta 9 noticias
@app.route('/noticias')
def noticias_destacadas():
    noticias = Noticia.query.order_by(Noticia.fecha.desc()).limit(9).all()
    return render_template("noticias.html", noticias=noticias)


# ==========================================================
# BIBLIOTECA
# ==========================================================

# Método para guardar un PDF
def save_pdf_file(f):
    if not f or getattr(f, 'filename', '') == '':
        return None

    # Nombre seguro
    filename = secure_filename(f.filename)
    ext = filename.rsplit('.', 1)[-1].lower()

    # Verificar extensión
    if ext != 'pdf':
        return None

    # Crear nombre único
    unique_name = f"{uuid.uuid4().hex}_{filename}"

    # Carpeta destino: static/libros/
    carpeta_libros = os.path.join(app.root_path, "static/uploads/libros")
    os.makedirs(carpeta_libros, exist_ok=True)

    # Guardar archivo
    f.save(os.path.join(carpeta_libros, unique_name))

    return unique_name



# Método para guardar portadas de documentos
def save_portada_file(file):
    if not file or file.filename == "":
        return None

    filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    path = os.path.join(app.root_path, "static/uploads/portadas", filename)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    file.save(path)

    return filename


# ------------------------------
# RUTAS
# ------------------------------

# LIBROS FÍSICOS
@app.route('/biblioteca/fisicos')
@requiere_login
def biblioteca_fisicos():
    libros = Biblioteca.query.filter_by(tipo_libro='fisico').all()
    return render_template('libros_fisicos.html', libros_fisicos=libros, body_class='libros-fisicos')


# LIBROS DIGITALES
@app.route('/biblioteca/digitales')
@requiere_login
def biblioteca_digitales():

    libros = Biblioteca.query.filter_by(tipo_libro='libro').all()

    # Filtro por titulación solo para TFG
    filtro_titulacion = request.args.get("titulacion", None)

    query_tfg = Biblioteca.query.filter_by(tipo_libro='tfg')

    if filtro_titulacion:
        query_tfg = query_tfg.filter_by(titulacion=filtro_titulacion)

    tfg_publicos = query_tfg.all()

    return render_template(
        'libros_digitales.html',
        libros=libros,
        tfg_publicos=tfg_publicos,
        filtro_titulacion=filtro_titulacion,
        body_class="libros-digitales"
    )


# ELIMINAR libro o TFG
@app.route('/biblioteca/eliminar/<int:item_id>', methods=['POST'])
@requiere_login
def biblioteca_eliminar(item_id):
    item = Biblioteca.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('biblioteca_digitales'))


# CREAR o EDITAR LIBRO/TFG
@app.route('/biblioteca/editar', methods=['GET', 'POST'])
@app.route('/biblioteca/editar/<int:item_id>', methods=['GET', 'POST'])
@requiere_login
def biblioteca_editar(item_id=None):

    item = Biblioteca.query.get(item_id) if item_id else None
    form = BibliotecaForm(obj=item)

    if item:
        form.publico.data = bool(item.publico)

    if form.validate_on_submit():

        # ------------------------------
        # GUARDAR PORTADA
        # ------------------------------
        portada_file = form.portada.data
        portada_filename = None

        if portada_file and portada_file.filename != "":
            portada_filename = save_portada_file(portada_file)

        # ------------------------------
        # PDF O LINK
        # ------------------------------
        tipo = form.tipo.data   # pdf o link
        filename = None
        enlace = None

        if tipo == 'pdf':
            archivo_pdf = form.archivo_pdf.data
            if archivo_pdf:
                filename = save_pdf_file(archivo_pdf)

            if not filename and not (item and item.archivo):
                flash("Debes subir un PDF válido.", "warning")
                return redirect(request.url)

        elif tipo == 'link':
            enlace = form.enlace.data
            if not enlace:
                flash("Debes introducir un enlace válido.", "warning")
                return redirect(request.url)

        # ------------------------------
        # ACTUALIZAR
        # ------------------------------
        if item:

            item.titulo = form.titulo.data
            item.descripcion = form.descripcion.data
            item.tipo = tipo
            item.enlace = enlace
            item.tipo_libro = form.tipo_libro.data
            item.publico = bool(form.publico.data)

            # Solo TFG lleva titulación
            item.titulacion = form.titulacion.data if item.tipo_libro == "tfg" else None

            if filename:
                item.archivo = filename
            if portada_filename:
                item.portada = portada_filename

        # ------------------------------
        # CREAR NUEVO
        # ------------------------------
        else:
            nuevo = Biblioteca(
                titulo=form.titulo.data,
                descripcion=form.descripcion.data,
                tipo=tipo,
                archivo=filename,
                enlace=enlace,
                tipo_libro=form.tipo_libro.data,
                publico=bool(form.publico.data),
                usuario_id=session['usuario_id'],
                portada=portada_filename,
                titulacion=form.titulacion.data if form.tipo_libro.data == "tfg" else None
            )

            db.session.add(nuevo)

        db.session.commit()
        flash("Elemento guardado correctamente.", "success")

        return redirect(url_for('biblioteca_digitales'))

    return render_template('biblioteca_editar.html', form=form, item=item, body_class="libros-digitales")


# Ruta libro en físico


# Agregar libro físico
@app.route('/biblioteca/fisicos/agregar', methods=['GET', 'POST'])
@requiere_login
def agregar_libro_fisico():
    form = LibroFisicoForm()
    
    if form.validate_on_submit():
        # Guardar portada si se sube
        portada_file = form.portada.data
        portada_filename = None
        if portada_file and portada_file.filename != "":
            nombre_original = secure_filename(portada_file.filename)
            portada_filename = f"{uuid.uuid4().hex}_{nombre_original}"
            
            # Carpeta de portadas para libros físicos
            carpeta_portadas = os.path.join(app.root_path, "static/uploads/libros")
            os.makedirs(carpeta_portadas, exist_ok=True)
            
            # Guardar archivo en disco
            portada_file.save(os.path.join(carpeta_portadas, portada_filename))
        
        # Crear nuevo libro físico
        nuevo_libro = Biblioteca(
            titulo=form.titulo.data,
            descripcion=form.descripcion.data,
            tipo='fisico',          # Obligatorio para la DB
            tipo_libro='fisico',    # Marca que es libro físico
            portada=portada_filename, # Nombre de archivo
            usuario_id=session['usuario_id'],
            publico=True             # Opcional, por defecto público
        )

        db.session.add(nuevo_libro)
        db.session.commit()
        flash("Libro físico agregado correctamente.", "success")
        return redirect(url_for('biblioteca_fisicos'))

    return render_template('agregar_libro_fisico.html', form=form, body_class="libros-fisicos")


# Eliminar libro físico
@app.route('/biblioteca/fisicos/eliminar/<int:item_id>', methods=['POST'])
@requiere_login
def eliminar_libro_fisico(item_id):
    libro = Biblioteca.query.get_or_404(item_id)
    # Opcional: eliminar archivo de portada del disco
    if libro.portada:
        ruta_portada = os.path.join(app.root_path, "static/uploads/libros", libro.portada)
        if os.path.exists(ruta_portada):
            os.remove(ruta_portada)
    db.session.delete(libro)
    db.session.commit()
    flash("Libro físico eliminado.", "success")
    return redirect(url_for('biblioteca_page'))

# Editar libro fisico
# Editar libro físico
@app.route('/biblioteca/fisicos/editar/<int:item_id>', methods=['GET', 'POST'])
@requiere_login
def editar_libro_fisico(item_id):
    libro = Biblioteca.query.get_or_404(item_id)
    form = LibroFisicoForm(obj=libro)  # Carga los datos actuales en el formulario

    if form.validate_on_submit():
        # Actualizar título y descripción
        libro.titulo = form.titulo.data
        libro.descripcion = form.descripcion.data

        # Guardar nueva portada si se sube
        portada_file = form.portada.data
        if portada_file and portada_file.filename != "":
            # Eliminar portada anterior del disco (opcional)
            if libro.portada:
                ruta_portada_ant = os.path.join(app.root_path, "static/uploads/libros", libro.portada)
                if os.path.exists(ruta_portada_ant):
                    os.remove(ruta_portada_ant)

            # Guardar nueva portada
            nombre_original = secure_filename(portada_file.filename)
            portada_filename = f"{uuid.uuid4().hex}_{nombre_original}"
            carpeta_portadas = os.path.join(app.root_path, "static/uploads/libros")
            os.makedirs(carpeta_portadas, exist_ok=True)
            portada_file.save(os.path.join(carpeta_portadas, portada_filename))
            libro.portada = portada_filename

        db.session.commit()
        flash("Libro físico actualizado correctamente.", "success")
        return redirect(url_for('biblioteca_fisicos'))

    return render_template('agregar_libro_fisico.html', form=form, editar=True)



# SOLICITAR PRESTAMO DEL LIBRP
@app.route('/biblioteca/fisicos/prestamo/<int:id>', methods=['GET', 'POST'])
@requiere_login
def solicitar_prestamo(id):
    libro = Biblioteca.query.get_or_404(id)
    form = SolicitudPrestamoForm()

    if form.validate_on_submit():
        # Datos del usuario desde la sesión
        nombre = session.get('nombre')
        apellidos = session.get('apellidos')
        dip = session.get('dip')
        correo = session.get('correo')
        fecha_envio = datetime.utcnow()
        motivo = form.motivo.data

        msg = Message(
            subject=f"Solicitud de préstamo: {libro.titulo}",
            sender=correo,
            recipients=["bibliotecario@universidad.com"],  # correo del bibliotecario
            body=f"""
Solicitud de préstamo de libro:

Libro: {libro.titulo}
Solicitante: {nombre} {apellidos}
DIP: {dip}
Correo: {correo}
Fecha: {fecha_envio.strftime('%d/%m/%Y %H:%M')}
Motivo: {motivo}
"""
        )
        mail.send(msg)

        flash("Solicitud enviada correctamente.", "success")
        return redirect(url_for('biblioteca_fisicos'))

    return render_template('solicitud_prestamo.html', form=form, libro=libro, body_class="prestar-libro")




# =========================================================
# SELECTIVIDAD
# =========================================================

# 1. LISTADO GENERAL (Vista de cuadrícula tipo noticias)
@app.route('/selectividad')
def selectividad():
    # Buscamos todos los registros
    datos = Selectividad.query.order_by(Selectividad.fecha_publicacion.desc()).all()
    
    # Pasamos 'resultados' al HTML para que el bucle {% for res in resultados %} funcione
    return render_template('selectividad_listado.html', resultados=datos)

# 2. DETALLE DE UNA NOTICIA (Vista individual al hacer clic)
@app.route('/selectividad/<int:id>', methods=['GET', 'POST'])
def selectividad_detalle(id):
    # Buscamos la noticia específica por ID
    resultado = Selectividad.query.get_or_404(id)
    form_opinion = OpinionForm()

    # Lógica para recibir comentarios en la noticia
    if form_opinion.validate_on_submit():
        nueva_opinion = OpinionSelectividad(
            nombre_usuario=form_opinion.nombre.data,
            comentario=form_opinion.mensaje.data,
            selectividad_id=id
        )
        db.session.add(nueva_opinion)
        db.session.commit()
        flash("Tu opinión ha sido publicada.", "success")
        return redirect(url_for('selectividad_detalle', id=id))

    return render_template('selectividad_detalle.html', resultado=resultado, form=form_opinion)

# 3. FORMULARIO DE SUBIDA (Solo administrador)
@app.route('/subir-selectividad', methods=['GET', 'POST'])
@requiere_login
@requiere_rol('administrador')
def subir_selectividad():
    form = SelectividadForm()
    
    if form.validate_on_submit():
        # Guardar el PDF
        archivo_pdf = form.pdf_file.data
        nombre_pdf = guardar_archivo(archivo_pdf, 'pdfs_selectividad') 
        
        # Guardar la Foto (si existe)
        nombre_foto = None
        if form.foto_examen.data:
            archivo_foto = form.foto_examen.data
            nombre_foto = guardar_archivo(archivo_foto, 'fotos_selectividad')

        # Crear el registro en la DB
        nueva_entrada = Selectividad(
            titulo=form.titulo.data,
            comentario_admin=form.comentario_admin.data,
            ruta_pdf=nombre_pdf,
            ruta_foto=nombre_foto,
            ruta_pie_foto=form.pie_foto.data,
            fecha_publicacion=datetime.utcnow()
        )
        
        db.session.add(nueva_entrada)
        db.session.commit()
        
        flash("Resultados publicados con éxito", "success")
        return redirect(url_for('selectividad'))

    return render_template('subir_selectividad.html', form=form)

# 4. ELIMINAR OPINIÓN (Solo administrador)
@app.route('/eliminar-opinion/<int:id>')
@requiere_login
@requiere_rol('administrador')
def eliminar_opinion(id):
    opinion = OpinionSelectividad.query.get_or_404(id)
    id_noticia = opinion.selectividad_id
    db.session.delete(opinion)
    db.session.commit()
    flash("Comentario eliminado correctamente.", "warning")
    return redirect(url_for('selectividad_detalle', id=id_noticia))



# =========================================================
# SOLICITUD DE MATRICULA. ESTUDIANTES NUEVOS, EGRESADOS, CONTINUANTES
# =========================================================
@app.route('/solicitar-matricula', methods=['GET', 'POST'])
def solicitar_matricula():
    form = MatriculaForm()
    
    if form.validate_on_submit():
        try:
            # A. Procesar archivos dinámicamente
            files_data = {}
            file_fields = [
                'doc_dni', 'doc_cert_selectividad', 'doc_instancia', 'doc_hoja_bachillerato',
                'doc_foto_carnet', 'doc_conducta_comunidad', 'doc_conducta_centro',
                'doc_ficha_matricula', 'doc_ficha_permanencia', 'doc_hoja_facultad',
                'doc_acta_defensa', 'doc_convalidaciones', 'doc_homologacion'
            ]

            for field in file_fields:
                file_storage = getattr(form, field).data
                if file_storage:
                    files_data[field] = guardar_archivo(file_storage, 'matriculas_docs')
                else:
                    files_data[field] = None

            # B. Crear registro en BD
            nueva_solicitud = SolicitudMatricula(
                tipo_estudiante=form.tipo_estudiante.data,
                nombre=form.nombre.data,
                apellidos=form.apellidos.data,
                fecha_nacimiento=form.fecha_nacimiento.data,
                residencia=form.residencia.data,
                natural_de=form.natural_de.data,
                dni_numero=form.dni_numero.data,
                email=form.email.data,
                carrera=form.carrera.data,
                telefono=form.telefono.data,
                sexo=form.sexo.data,           
                nacionalidad=form.nacionalidad.data,
                **files_data # Pasa todos los archivos del diccionario de golpe
                )
                
            db.session.add(nueva_solicitud)
            db.session.commit()

            # CORREO AUTOMATICO QUE LLEGA TRAS COMPLETAR LA SOLICITUD::
            enviar_acuse_recibo(solicitud=nueva_solicitud, dominio=request.host_url.rstrip('/'))
        

            # Redirigir a Éxito
            return redirect(url_for('pago_exitoso', 
                                    nombre=form.nombre.data, 
                                    apellidos=form.apellidos.data, 
                                    carrera=form.carrera.data))

        except Exception as e:
            db.session.rollback()
            return redirect(url_for('pago_error', mensaje=f"Error en base de datos: {str(e)}"))

    # Manejo de errores de validación (Si falta un campo obligatorio)
    if request.method == 'POST':
        errores = [f"{getattr(form, f).label.text}: {m[0]}" for f, m in form.errors.items()]
        return redirect(url_for('pago_error', mensaje=" | ".join(errores)))

    return render_template('solicitar_matricula.html', form=form)


# RUTA DE ÉXITO
@app.route('/inscripcion-exitosa')
def pago_exitoso(): # <--- Este es el 'endpoint'
    datos = {
        'nombre': request.args.get('nombre'),
        'apellidos': request.args.get('apellidos'),
        'carrera': request.args.get('carrera')
    }
    return render_template('inscripcion_ok.html', datos=datos)

# RUTA DE ERROR
@app.route('/error-inscripcion')
def pago_error(): # <--- Asegúrate de que se llame exactamente así
    mensaje = request.args.get('mensaje', 'Error desconocido en el formulario')
    return render_template('inscripcion_error.html', mensaje=mensaje)


# 1. LISTADO GENERAL
@app.route('/admin/ver-matriculas')
def ver_matriculas():
    solicitudes = SolicitudMatricula.query.order_by(SolicitudMatricula.fecha_creacion.desc()).all()
    return render_template('admin_matriculas.html', solicitudes=solicitudes)


# ADMITIR ALUMNO
@app.route('/admin/matricula/estado/<int:id>/Admitido')
def admitir_alumno(id):
    solicitud = SolicitudMatricula.query.get_or_404(id)
    solicitud.estado = 'Admitido'
    db.session.commit()

    # Definimos el dominio aquí
    dominio = "http://localhost:5000"
    
    # Pasamos el dominio a la función (asegúrate de que la función lo acepte)
    try:
        enviar_confirmacion_matricula(solicitud, dominio)
        flash("Alumno admitido y notificado", "success")
    except Exception as e:
        flash(f"Error al enviar correo: {str(e)}", "warning")
    
    return redirect(url_for('ver_matriculas'))


# SOLICITAR REVISION.
@app.route('/admin/matricula/estado/<int:id>/Revision')
def solicitar_revision(id):
    # 1. Buscamos la solicitud en la base de datos
    solicitud = SolicitudMatricula.query.get_or_404(id)
    
    # 2. Actualizamos el estado
    solicitud.estado = 'Revision'
    db.session.commit()

    # 3. LLAMADA AL NUEVO AVISO:
    # Pasamos el objeto 'solicitud' completo, el dominio automático y un comentario opcional
    enviar_aviso_revision(
        solicitud=solicitud, 
        dominio=request.host_url.rstrip('/'),
        comentario="Algunos documentos son ilegibles o están incompletos. Por favor, revísalos y vuelve a subirlos."
    )
    
    flash(f"La solicitud #{id} ha sido marcada para revisión y se ha enviado el correo al alumno.", "warning")
    return redirect(url_for('ver_matriculas'))


# PERMITIR DESCARGAR PDF SI EL ALUMNO ES ADMITIDO
@app.route('/descargar-admision/<int:id>')
def descargar_admision(id):
    # 1. Buscamos la solicitud en la base de datos
    solicitud = SolicitudMatricula.query.get_or_404(id)
    
    # 2. Verificación de seguridad: Solo admitidos pueden descargar
    if solicitud.estado != 'Admitido':
        # Si intenta descargar sin estar admitido, lanzamos error 403 (Prohibido)
        return """
        <div style="text-align:center; margin-top:50px; font-family:Arial;">
            <h1 style="color:red;">Acceso Denegado</h1>
            <p>Tu solicitud aún está en proceso de revisión o no ha sido admitida.</p>
            <a href="/">Volver al inicio</a>
        </div>
        """, 403

    try:
        # 3. Llamamos a la función que creamos antes (que devuelve el BytesIO)
        pdf_buffer = generar_pdf_admision(solicitud)
        
        # 4. Enviamos el archivo al navegador
        # as_attachment=True fuerza la descarga
        # download_name es el nombre que verá el alumno al guardar el archivo
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"Resguardo_Admision_{solicitud.nombre}_{solicitud.id}.pdf"
        )

    except Exception as e:
        # En caso de error técnico (ej. falta una librería), lo registramos
        logging.error(f"Error generando PDF para ID {id}: {e}")
        return f"Hubo un error al generar tu certificado: {str(e)}", 500

# 3. EXPORTACIÓN A EXCEL
@app.route('/admin/exportar-matriculas')
@requiere_login
@requiere_rol('administrador')
def exportar_matriculas():
    solicitudes = SolicitudMatricula.query.all()
    data = [{
        'Fecha': s.fecha_creacion.strftime('%d/%m/%Y'),
        'Estudiante': f"{s.nombre} {s.apellidos}",
        'DNI': s.dni_numero,
        'Carrera': s.carrera,
        'Estado': s.estado
    } for s in solicitudes]
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name='Matriculas_UNGE.xlsx')


# ========================================================
# CORREOS DE LA UNIVERSIDAD PARA LA MATRICULA
# ========================================================

# Estructura de un mensaje si la matricula es aceptada. GMAIL/OUTLOOK
def enviar_confirmacion_matricula(solicitud, dominio):
    """
    Envía un correo de admisión con diseño institucional.
    Usa el objeto 'solicitud' para obtener los datos reales de la BD.
    """
    # Extraemos los datos del objeto solicitud
    email_destino = solicitud.email
    nombre_alumno = f"{solicitud.nombre} {solicitud.apellidos}"
    id_solicitud = solicitud.id
    dni_alumno = solicitud.dni_numero
    carrera_alumno = solicitud.carrera

    msg = MIMEMultipart('alternative')
    msg['From'] = f"Secretaría Académica UNGE <{CORREO_MATRICULAS_USER}>"
    msg['To'] = email_destino
    msg['Subject'] = f"¡FELICIDADES! Has sido admitido en la UNGE - Ref: {id_solicitud}"

    # Construcción del HTML con un bloque de mensaje elegante
    html_content = f"""
    <html>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7f9;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse; background-color: #ffffff; margin-top: 30px; border-radius: 15px; border: 1px solid #e1e8ed; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            
            <tr>
                <td align="center" style="padding: 40px 0 20px 0; background-color: #ffffff;">
                    <img src="{dominio}/static/img/logo_unge.jpeg" alt="Logo UNGE" width="100" style="display: block; margin-bottom: 15px;">
                    <h1 style="margin: 0; font-size: 14px; color: #1a237e; letter-spacing: 1px; text-transform: uppercase;">Universidad Nacional de Guinea Ecuatorial</h1>
                    <p style="margin: 5px 0 0 0; font-size: 16px; color: #ff6f00; font-weight: bold;">Facultad de Ciencias de la Salud</p>
                </td>
            </tr>

            <tr>
                <td style="padding: 20px 40px; text-align: center; background-color: #1a237e;">
                    <h2 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 300;">¡ADMISIÓN CONFIRMADA!</h2>
                </td>
            </tr>

            <tr>
                <td style="padding: 40px 40px 20px 40px;">
                    <p style="font-size: 18px; color: #2c3e50; margin-bottom: 25px;">Estimado/a <strong>{nombre_alumno}</strong>,</p>
                    
                    <p style="font-size: 15px; color: #546e7a; line-height: 1.6; margin-bottom: 25px;">
                        Es un placer para nosotros informarle que, tras la revisión exhaustiva de su expediente académico y documentación presentada, 
                        ha sido formalmente <strong>ACEPTADO</strong> para cursar estudios en nuestra institución.
                    </p>

                    <div style="background-color: #f8fafb; border-radius: 10px; padding: 25px; border-left: 5px solid #ff6f00; margin-bottom: 30px;">
                        <table width="100%" style="font-size: 14px; color: #37474f;">
                            <tr>
                                <td style="padding-bottom: 10px;"><strong>Nº DE EXPEDIENTE:</strong></td>
                                <td style="padding-bottom: 10px; text-align: right;">#{id_solicitud}</td>
                            </tr>
                            <tr>
                                <td style="padding-bottom: 10px;"><strong>TIPO DE MATRÍCULA:</strong></td>
                                <td style="padding-bottom: 10px; text-align: right; color: #ff6f00;">{solicitud.tipo_estudiante}</td>
                            </tr>
                            <tr>
                                <td style="padding-bottom: 10px;"><strong>DOCUMENTO IDENTIDAD:</strong></td>
                                <td style="padding-bottom: 10px; text-align: right;">{dni_alumno}</td>
                            </tr>
                            <tr>
                                <td><strong>CARRERA ASIGNADA:</strong></td>
                                <td style="text-align: right; color: #1a237e; font-weight: bold;">{carrera_alumno}</td>
                            </tr>
                        </table>
                    </div>

                    <p style="font-size: 14px; color: #455a64; margin-bottom: 30px; text-align: center;">
                        Para completar su proceso de matriculación, debe descargar su <strong>Resguardo de Admisión</strong> y presentarlo en la secretaría Edi. II de la Facultad para el pago de tasas.
                    </p>

                    <div style="text-align: center; margin: 20px 0 40px 0;">
                        <a href="{dominio}/descargar-admision/{id_solicitud}" 
                           style="background-color: #ff6f00; color: #ffffff; padding: 18px 35px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 15px; display: inline-block; box-shadow: 0 4px 6px rgba(255,111,0,0.2);">
                           OBTENER MI RESGUARDO DE ADMISIÓN
                        </a>
                    </div>
                </td>
            </tr>

            <tr>
                <td style="background-color: #eceff1; padding: 30px; text-align: center; border-top: 1px solid #cfd8dc;">
                    <p style="margin: 0; color: #78909c; font-size: 12px; line-height: 1.5;">
                        <strong>Secretaría Académica - Facultad de Ciencias de la Salud</strong><br>
                        Campus de Bata, Guinea Ecuatorial<br>
                        Este es un mensaje automático, por favor no responda a este correo.
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP(CORREO_MATRICULAS_SERVER, CORREO_MATRICULAS_PORT)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False

# --------------------------------------------------------------------------
# Mensaje automatico que se recibe tras solicitar matricula
def enviar_acuse_recibo(solicitud, dominio):
    """
    Envía un correo de confirmación de recepción con el diseño institucional.
    Usa el objeto 'solicitud' para mantener la coherencia con enviar_confirmacion_matricula.
    """
    email_destino = solicitud.email
    nombre_alumno = f"{solicitud.nombre} {solicitud.apellidos}"
    id_solicitud = solicitud.id
    carrera_alumno = solicitud.carrera

    msg = MIMEMultipart('alternative')
    msg['From'] = f"Secretaría Académica UNGE <{CORREO_MATRICULAS_USER}>"
    msg['To'] = email_destino
    msg['Subject'] = f"Solicitud de Matrícula Recibida - Ref: {id_solicitud}"

    html_content = f"""
    <html>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7f9;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse; background-color: #ffffff; margin-top: 30px; border-radius: 15px; border: 1px solid #e1e8ed; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            
            <tr>
                <td align="center" style="padding: 40px 0 20px 0; background-color: #ffffff;">
                    <img src="{dominio}/static/img/logo_unge.jpeg" alt="Logo UNGE" width="100" style="display: block; margin-bottom: 15px;">
                    <h1 style="margin: 0; font-size: 14px; color: #1a237e; letter-spacing: 1px; text-transform: uppercase;">Universidad Nacional de Guinea Ecuatorial</h1>
                    <p style="margin: 5px 0 0 0; font-size: 16px; color: #ff6f00; font-weight: bold;">Facultad de Ciencias de la Salud</p>
                </td>
            </tr>

            <tr>
                <td style="padding: 20px 40px; text-align: center; background-color: #1a237e;">
                    <h2 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: 300; letter-spacing: 1px;">SOLICITUD RECIBIDA</h2>
                </td>
            </tr>

            <tr>
                <td style="padding: 40px 40px 20px 40px;">
                    <p style="font-size: 18px; color: #2c3e50; margin-bottom: 25px;">Estimado/a <strong>{nombre_alumno}</strong>,</p>
                    
                    <p style="font-size: 15px; color: #546e7a; line-height: 1.6; margin-bottom: 25px;">
                        Le confirmamos que hemos recibido correctamente sus datos y documentos para la inscripción en la carrera de <strong>{carrera_alumno}</strong>. 
                        Su solicitud ha entrado en fase de revisión por parte de la Secretaría Académica.
                    </p>

                    <div style="background-color: #f8fafb; border-radius: 10px; padding: 25px; border-left: 5px solid #1a237e; margin-bottom: 30px;">
                        <table width="100%" style="font-size: 14px; color: #37474f;">
                            <tr>
                                <td style="padding-bottom: 10px;"><strong>Nº DE REFERENCIA:</strong></td>
                                <td style="padding-bottom: 10px; text-align: right; font-weight: bold;">#{id_solicitud}</td>
                            </tr>
                            <tr>
                                <td style="padding-bottom: 10px;"><strong>ESTADO ACTUAL:</strong></td>
                                <td style="padding-bottom: 10px; text-align: right; color: #ff6f00; font-weight: bold;">En Revisión</td>
                            </tr>
                            <tr>
                                <td><strong>CARRERA SOLICITADA:</strong></td>
                                <td style="text-align: right; color: #1a237e;">{carrera_alumno}</td>
                            </tr>
                        </table>
                    </div>

                    <p style="font-size: 14px; color: #455a64; margin-bottom: 30px; line-height: 1.6;">
                        <strong>¿Qué sigue ahora?</strong><br>
                        Nuestro equipo verificará que toda la documentación cargada sea legible y válida. Una vez finalizada la revisión, recibirá un nuevo correo electrónico indicando si su solicitud ha sido <strong>admitida</strong> o si requiere alguna corrección.
                    </p>

                    <p style="font-size: 13px; color: #78909c; text-align: center; font-style: italic;">
                        No es necesario que realice ninguna otra acción por el momento.
                    </p>
                </td>
            </tr>

            <tr>
                <td style="background-color: #eceff1; padding: 30px; text-align: center; border-top: 1px solid #cfd8dc;">
                    <p style="margin: 0; color: #78909c; font-size: 12px; line-height: 1.5;">
                        <strong>Secretaría Académica - Facultad de Ciencias de la Salud</strong><br>
                        Campus de Bata, Guinea Ecuatorial<br>
                        Este es un mensaje automático, por favor no responda a este correo.
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP(CORREO_MATRICULAS_SERVER, CORREO_MATRICULAS_PORT)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error al enviar acuse de recibo: {e}")
        return False

# -----------------------------------------------------------------
# GENERAR EN DOCUMENTOS DESCARGABLES LA INFORMACION DE LOS USUARIOS
def generar_pdf_admision(solicitud):
    # Usamos FPDF en modo estándar
    pdf = FPDF()
    pdf.add_page()

    # --- INSERTAR LOGO ---
    # Buscamos la ruta absoluta de la imagen en tu carpeta static
    ruta_logo = os.path.join(current_app.root_path, 'static', 'img', 'logo_unge.jpeg')
    
    try:
        # image(ruta, x, y, ancho)
        pdf.image(ruta_logo, 10, 8, 25) 
    except Exception as e:
        print(f"No se pudo cargar el logo: {e}")
    
    # Encabezado UNGE
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="UNIVERSIDAD NACIONAL DE GUINEA ECUATORIAL", ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="FACULTAD DE CIENCIAS DE LA SALUD", ln=True, align='C')
    pdf.ln(10)
    
    # Título del documento
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 12, txt="RESGUARDO DE ADMISIÓN", ln=True, align='C', fill=True)
    pdf.ln(10)
    
    # Datos del Alumno - Limpiamos caracteres extraños con .encode().decode() si es necesario
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, txt=f"ID de Solicitud: #00{solicitud.id}", ln=True)
    pdf.cell(0, 10, txt=f"Nombre Completo: {solicitud.nombre} {solicitud.apellidos}", ln=True)
    pdf.cell(0, 10, txt=f"DNI / Pasaporte: {solicitud.dni_numero}", ln=True)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt=f"Tipo de Estudiante: {solicitud.tipo_estudiante.upper()}", ln=True)
    pdf.cell(0, 10, txt=f"Carrera: {solicitud.carrera}", ln=True)
    pdf.ln(5)
    
    # Estado
    pdf.set_text_color(0, 128, 0) # Verde institucional
    pdf.cell(0, 10, txt="ESTADO: ADMITIDO / APROBADO", ln=True)
    pdf.set_text_color(0, 0, 0)
    
    pdf.ln(15)
    pdf.set_font("Arial", 'I', 10)
    text_footer = ("Este documento acredita que el estudiante ha sido aceptado oficialmente. "
                   "Debe presentarse en la Secretaría de la Facultad para formalizar el pago.")
    pdf.multi_cell(0, 10, txt=text_footer)
    
    pdf.ln(20)
    # Fecha y Firma
    pdf.cell(0, 10, f"Fecha de emision: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='R')
    pdf.ln(20)
    pdf.cell(0, 10, "__________________________", ln=True, align='C')
    pdf.cell(0, 7, "Sello y Firma de Secretaria Academica", ln=True, align='C')

    # EXPLICACIÓN DEL FIX:
    # 1. Obtenemos el output como string 'S'
    # 2. Lo codificamos a latin-1 ignorando caracteres que FPDF no soporte
    # 3. Lo metemos en BytesIO para que send_file lo vea como un ARCHIVO BINARIO
    output = pdf.output(dest='S').encode('latin-1', 'ignore')
    buffer = io.BytesIO(output)
    buffer.seek(0) # Ponemos el puntero al inicio para que Flask lea desde el principio
    
    return buffer


#-------------------------------------------------------------------
# FUNCION PARA LA DOCUMENTACION INCOMPLETA. MATRICULA-SECRETARIA
def enviar_aviso_revision(solicitud, dominio, comentario="No especificado"):
    """
    Envía un correo informando que la documentación es incorrecta.
    Permite incluir una nota del administrador explicando el error.
    """
    email_destino = solicitud.email
    nombre_alumno = f"{solicitud.nombre} {solicitud.apellidos}"
    id_solicitud = solicitud.id

    msg = MIMEMultipart('alternative')
    msg['From'] = f"Secretaría Académica UNGE <{CORREO_MATRICULAS_USER}>"
    msg['To'] = email_destino
    msg['Subject'] = f"ACCIÓN REQUERIDA: Documentación Incompleta - Ref: {id_solicitud}"

    html_content = f"""
    <html>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7f9;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse; background-color: #ffffff; margin-top: 30px; border-radius: 15px; border: 1px solid #e1e8ed; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            
            <tr>
                <td align="center" style="padding: 40px 0 20px 0; background-color: #ffffff;">
                    <img src="{dominio}/static/img/logo_unge.jpeg" alt="Logo UNGE" width="100" style="display: block; margin-bottom: 15px;">
                    <h1 style="margin: 0; font-size: 14px; color: #1a237e; letter-spacing: 1px; text-transform: uppercase;">Universidad Nacional de Guinea Ecuatorial</h1>
                    <p style="margin: 5px 0 0 0; font-size: 16px; color: #ff6f00; font-weight: bold;">Facultad de Ciencias de la Salud</p>
                </td>
            </tr>

            <tr>
                <td style="padding: 20px 40px; text-align: center; background-color: #ff6f00;">
                    <h2 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: 300; letter-spacing: 1px;">DOCUMENTACIÓN PENDIENTE</h2>
                </td>
            </tr>

            <tr>
                <td style="padding: 40px 40px 20px 40px;">
                    <p style="font-size: 18px; color: #2c3e50; margin-bottom: 25px;">Hola <strong>{nombre_alumno}</strong>,</p>
                    
                    <p style="font-size: 15px; color: #546e7a; line-height: 1.6; margin-bottom: 25px;">
                        Hemos revisado su solicitud <strong>#{id_solicitud}</strong> y lamentamos informarle que su expediente está 
                        <span style="color: #d32f2f; font-weight: bold;">INCOMPLETO</span> o contiene documentos que no han podido ser validados.
                    </p>

                    <div style="background-color: #fff3e0; border-radius: 10px; padding: 25px; border-left: 5px solid #ff6f00; margin-bottom: 30px;">
                        <p style="margin: 0 0 10px 0; font-size: 14px; color: #e65100; font-weight: bold;">OBSERVACIONES DE SECRETARÍA:</p>
                        <p style="margin: 0; font-size: 15px; color: #3e2723; font-style: italic;">
                            "{comentario}"
                        </p>
                    </div>

                    <p style="font-size: 14px; color: #455a64; margin-bottom: 30px; line-height: 1.6;">
                        <strong>¿Cómo solucionar esto?</strong><br>
                        Debe acudir a la Secretaría de la Facultad o volver a realizar el proceso de carga de documentos asegurándose de que los archivos sean legibles, estén en formato PDF y correspondan a lo solicitado.
                    </p>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{dominio}/solicitar-matricula" 
                           style="background-color: #1a237e; color: #ffffff; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 14px; display: inline-block;">
                            VOLVER AL FORMULARIO DE MATRÍCULA
                        </a>
                    </div>
                </td>
            </tr>

            <tr>
                <td style="background-color: #eceff1; padding: 30px; text-align: center; border-top: 1px solid #cfd8dc;">
                    <p style="margin: 0; color: #78909c; font-size: 12px; line-height: 1.5;">
                        <strong>Secretaría Académica - Facultad de Ciencias de la Salud</strong><br>
                        Campus de Bata, Guinea Ecuatorial<br>
                        Si tiene dudas, por favor contacte con nosotros directamente.
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP(CORREO_MATRICULAS_SERVER, CORREO_MATRICULAS_PORT)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error al enviar aviso de revisión: {e}")
        return False
# ----------------------------------------------------------------


# ==========================================================
# EXPEDIENTE ACADEMICO
# ==========================================================
# RUTA 1: Ver el expediente y los cálculos
@app.route('/expediente/')
@app.route('/expediente/<int:id>')
@login_required
def ver_expediente(id=None):
    # 1. Determinamos qué perfil ver: si no hay ID, vemos el nuestro
    target_id = id if id is not None else current_user.id
    
    # 2. Buscamos al usuario dueño del perfil
    usuario_perfil = Usuario.query.get_or_404(target_id)
    
    # 3. Buscamos (o creamos) su registro en la tabla Estudiante
    estudiante = Estudiante.query.filter_by(usuario_id=target_id).first()
    
    if not estudiante:
        # Aquí ya no dará TypeError porque añadiste 'carrera' a la Clase Estudiante
        estudiante = Estudiante(
            usuario_id=target_id, 
            matricula=f"MAT-{target_id}", 
            carrera=usuario_perfil.carrera # Valor inicial desde Usuario
        )
        db.session.add(estudiante)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return f"Error al crear registro de estudiante: {e}", 500

    # 4. Traemos sus notas de la tabla Expediente
    registros = Expediente.query.filter_by(estudiante_id=estudiante.id).all()
    
    # 5. Cálculos para la vista
    puntuacion = sum(r.nota_final for r in registros)
    total_materias = len(registros)
    promedio = round(puntuacion / total_materias, 2) if total_materias > 0 else 0

    # 6. Seguridad: Solo puedes editar si estás viendo tu propio expediente
    puedo_editar = (current_user.id == target_id)

    return render_template(
        'expediente.html', 
        usuario=usuario_perfil, 
        estudiante=estudiante, # Pasamos el objeto estudiante para usar 'estudiante.carrera'
        registros=registros, 
        puntuacion=puntuacion, 
        aprobado=promedio, # Usamos el promedio calculado
        puedo_editar=puedo_editar
    )

# RUTA 2: Procesar la firma de la nota
@app.route('/firmar-nota/<int:nota_id>')
@login_required
def firmar_nota(nota_id):
    nota = Expediente.query.get_or_404(nota_id)
    
    # CUIDADO: nota.estudiante.usuario_id debe coincidir con current_user.id
    # Buscamos al estudiante dueño de esa nota
    estudiante_propietario = Estudiante.query.get(nota.estudiante_id)

    if estudiante_propietario.usuario_id != current_user.id:
        flash("No puedes firmar un expediente que no es el tuyo.", "danger")
        return redirect(url_for('ver_expediente', usuario_id=estudiante_propietario.usuario_id))

    nota.firmado = True
    nota.fecha_firma = datetime.now()
    db.session.commit()
    return redirect(url_for('ver_expediente'))


# ==========================================================
# PANEL OFICIAL PARA PROFESORES
# ==========================================================
# Un estudiante no puede entrar
@app.errorhandler(403)
def access_denied(error):
    return render_template('errors/403.html'), 403



# SUBIR NOTAS EN EXEL
@app.route('/subir_notas', methods=['POST'])
@login_required
def subir_notas():
    if 'archivo_excel' not in request.files:
        flash("No se seleccionó ningún archivo", "warning")
        return redirect(request.url)
    
    file = request.files['archivo_excel']
    if file.filename == '':
        return redirect(request.url)

    if file:
        df = pd.read_excel(file)
        
        # Ejemplo de estructura esperada en Excel: 
        # Columnas: [matricula, asignatura, nota, anio]
        
        for index, row in df.iterrows():
            # Buscamos al estudiante por matrícula
            estudiante = Estudiante.query.filter_by(matricula=row['matricula']).first()
            
            if estudiante:
                nuevo_registro = Expediente(
                    estudiante_id=estudiante.id,
                    asignatura_nombre=row['asignatura'],
                    nota_final=row['nota'],
                    anio_academico=row['anio'],
                    firmado=True,
                    fecha_firma=datetime.utcnow()
                )
                db.session.add(nuevo_registro)
        
        db.session.commit()
        flash("Notas procesadas y publicadas correctamente", "success")
        
    return redirect(url_for('panel_profesor'))



# REGISTRO DE PROFESORES
# ==========================================================
# RUTAS DEL PROFESOR (Registro, Activación y Panel)
# ==========================================================

# Definimos las variables de ruta (igual que hacías antes)
UPLOAD_FOLDER_DIP = os.path.join('static', 'uploads', 'dips')
UPLOAD_FOLDER_FOTOS = os.path.join('static', 'uploads', 'fotos')

# 1. REGISTRO DEL PROFESOR
@app.route('/profesor/registro', methods=['GET', 'POST'])
def profesor_registro():
    if request.method == 'POST':
        # 1. Captura de datos
        email_personal = request.form.get('email_personal')
        dip_numero = request.form.get('dip_numero')
        
        # 2. Validaciones (Aspirante o Usuario existente)
        aspirante_existente = Profesor.query.filter_by(dip_aspirante=dip_numero).first()
        usuario_existente = Usuario.query.filter_by(dip=dip_numero).first()

        if aspirante_existente or usuario_existente:
            flash(f"El DIP {dip_numero} ya está registrado o tiene una solicitud pendiente.", "warning")
            return redirect(url_for('profesor_registro'))

        # 3. Manejo de Archivos
        dip_file = request.files.get('archivo_dip')
        foto_file = request.files.get('archivo_foto')
        
        if dip_file and foto_file:
            # --- CREACIÓN AUTOMÁTICA DE CARPETAS ---
            # Esto es lo que permite que se creen solas si no existen
            os.makedirs(UPLOAD_FOLDER_DIP, exist_ok=True)
            os.makedirs(UPLOAD_FOLDER_FOTOS, exist_ok=True)
            # ---------------------------------------

            nombre_dip = secure_filename(f"dip_{dip_numero}_{dip_file.filename}")
            nombre_foto = secure_filename(f"foto_{dip_numero}_{foto_file.filename}")
            
            # Guardamos usando las variables locales (SIN app.config)
            dip_file.save(os.path.join(UPLOAD_FOLDER_DIP, nombre_dip))
            foto_file.save(os.path.join(UPLOAD_FOLDER_FOTOS, nombre_foto))

            # 4. Crear el registro en la tabla Profesor (Aspirante)
            nuevo_aspirante = Profesor(
                nombre_aspirante=request.form.get('nombre'),
                apellidos_aspirante=request.form.get('apellidos'),
                correo_personal=email_personal,
                dip_aspirante=dip_numero,
                telefono_aspirante=request.form.get('telefono'),
                sexo_aspirante=request.form.get('sexo'),
                departamento=request.form.get('departamento'),
                especialidad=request.form.get('especialidad'),
                archivo_dip=nombre_dip,
                archivo_foto=nombre_foto,
                cuenta_activa=False 
            )
            
            try:
                db.session.add(nuevo_aspirante)
                db.session.commit()
                
                # Guardamos el ID en sesión para la página de pendiente
                session['aspirante_reciente_id'] = nuevo_aspirante.id
                
                enviar_correo_recepcion_profesor(nuevo_aspirante, request.host_url)
                
                flash("Solicitud enviada con éxito.", "success")
                return redirect(url_for('profesor_registro_pendiente'))
                
            except Exception as e:
                db.session.rollback()
                flash(f"Error al guardar: {str(e)}", "danger")
                return redirect(url_for('profesor_registro'))

    return render_template('profesor_registro.html')

# 2. MENSAJE QUE MUESTRA EL ENVIO DE FORMULARIO
@app.route('/profesor/registro/pendiente')
def profesor_registro_pendiente():
    # 1. Intentamos obtener el ID del ASPIRANTE (Profesor) guardado en el paso anterior
    aspirante_id = session.get('aspirante_reciente_id')
    
    if not aspirante_id:
        # Si no hay ID en sesión, redirigimos al inicio
        return redirect(url_for('index'))
    
    # 2. Buscamos en la tabla Profesor
    aspirante = Profesor.query.get(aspirante_id)
    
    if not aspirante:
        return redirect(url_for('index'))
    
    # 3. Pasamos el objeto 'aspirante' al HTML
    return render_template('profesor_registro_pendiente.html', aspirante=aspirante)

# 3. LUGAR PARA PODER ACTIVAR LA CUENTA
@app.route('/profesor/activar', methods=['GET', 'POST'])
def profesor_activar_cuenta():
    if request.method == 'POST':
        codigo_ingresado = request.form.get('codigo_activacion')
        nueva_password = request.form.get('nueva_password')
        confirmar_password = request.form.get('confirmar_password')
        
        # 1. Buscar al profesor por el código
        profe = Profesor.query.filter_by(codigo_activacion=codigo_ingresado).first()
        
        if not profe:
            flash("El código introducido no es válido o ya fue utilizado.", "danger")
            return redirect(url_for('profesor_activar_cuenta'))

        # 2. Validar que las contraseñas coincidan
        if nueva_password != confirmar_password:
            flash("Las contraseñas no coinciden. Inténtelo de nuevo.", "warning")
            return render_template('profesor_activar_cuenta.html', codigo=codigo_ingresado)

        # 3. Validar longitud mínima de contraseña
        if len(nueva_password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "warning")
            return render_template('profesor_activar_cuenta.html', codigo=codigo_ingresado)

        try:
            # 4. Actualizar el estado del Profesor
            profe.cuenta_activa = True
            profe.codigo_activacion = None  # El código queda inutilizable tras el éxito
            
            # 5. Actualizar la contraseña en la tabla Usuario vinculada
            usuario_vinculado = profe.usuario
            usuario_vinculado.set_password(nueva_password)
            
            db.session.commit()
            
            # Pasamos el objeto usuario para mostrar el correo institucional en el éxito
            return render_template('profesor_activacion_exito.html', usuario=usuario_vinculado)
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error al activar la cuenta: {str(e)}", "danger")
            
    return render_template('profesor_activar_cuenta.html')

# PANEL PRINCIPAL DEL PROFESOR
@app.route('/profesor/panel')
@requiere_login
@requiere_rol('profesor')
def profesor_panel():
    # Buscamos los datos específicos de la tabla Profesor vinculados al Usuario logueado
    datos_profe = Profesor.query.filter_by(usuario_id=current_user.id).first()
    
    if not datos_profe:
        flash("Error: No se encontró información de perfil docente.", "danger")
        return redirect(url_for('login_page'))
        
    return render_template('profesor_panel.html', profe=datos_profe)





# ==========================================================
# RUTAS DE ADMINISTRADOR (Gestión y Validación de Docentes)
# ==========================================================

@app.route('/admin/profesores/revision')
@login_required
def admin_profesor_revision():
    """Panel principal donde el admin ve a los profes que esperan validación"""
    if current_user.rol != 'admin':
        flash("Acceso denegado. Solo administradores.", "danger")
        return redirect(url_for('inicio'))
    
    # Solo traemos a los profesores cuya cuenta_activa es False
    solicitudes = Profesor.query.filter_by(cuenta_activa=False).all()
    return render_template('admin_profesor_revision.html', solicitudes=solicitudes)

# Validar al profesor
@app.route('/admin/profesores/validar/<int:id>', methods=['POST'])
@login_required
@requiere_rol("admin")
def admin_profesor_validar(id):
    profe = Profesor.query.get_or_404(id)
    
    try:
        # 1. GENERAR DATOS PRIMERO (Evita inconsistencias)
        # Generar Correo Institucional
        nombres = profe.nombre_aspirante.lower().split()
        iniciales = "".join([n[0] for n in nombres if n])
        primer_apellido = profe.apellidos_aspirante.lower().split()[0]
        correo_inst = f"{iniciales}.{primer_apellido}.2025@profesores.cienciasdelasalud.unge.gq"
        
        # Generar Código de Activación
        codigo = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

        # 2. CREAR USUARIO CON LOS DATOS FINALES
        nuevo_usuario = Usuario(
            nombre=profe.nombre_aspirante,
            apellidos=profe.apellidos_aspirante,
            correo=profe.correo_personal,
            correo_institucional=correo_inst,  # <--- LOGIN OFICIAL
            rol='profesor',
            dip=profe.dip_aspirante,
            telefono=profe.telefono_aspirante,
            sexo=profe.sexo_aspirante
        )
        nuevo_usuario.set_password(profe.dip_aspirante) 
        
        db.session.add(nuevo_usuario)
        db.session.flush() 

        # 3. VINCULAR Y ACTUALIZAR TABLA PROFESOR
        profe.usuario_id = nuevo_usuario.id 
        profe.codigo_activacion = codigo
        profe.cuenta_activa = False # Se activa cuando el use el código
        
        db.session.commit()
        
        # 4. ENVIAR CORREO (Asegúrate que enviar_activacion_profesor acepte estos 4 datos)
        enviar_activacion_profesor(profe, codigo, correo_inst, request.host_url)
        
        flash(f"Validación exitosa. Se ha enviado el código al correo personal del profesor.", "success")
        
    except Exception as e:
        db.session.rollback()
        print(f"ERROR EN VALIDACIÓN: {e}") # Importante revisar tu terminal
        flash(f"Error al validar: {str(e)}", "danger")
        
    return redirect(url_for('admin_profesor_revision'))


@app.route('/admin/profesores/rechazar/<int:id>', methods=['POST'])
@login_required
@requiere_rol("admin")
def admin_profesor_rechazar(id):
    """Rechaza la solicitud y borra los datos para permitir re-intento"""
    if current_user.rol != 'admin': return abort(403)
    
    profe = Profesor.query.get_or_404(id)
    usuario = profe.usuario
    motivo = request.form.get('motivo_rechazo')
    
    # 1. Notificar al profesor por correo
    enviar_rechazo_profesor(usuario, motivo, request.host_url)
    
    # 2. Eliminar registros y archivos asociados (Opcional pero recomendado)
    # Aquí podrías borrar los archivos de static/uploads si lo deseas
    db.session.delete(profe)
    db.session.delete(usuario)
    db.session.commit()
    
    flash("Solicitud denegada y registros eliminados.", "warning")
    return redirect(url_for('admin_profesor_revision'))

# ==========================================================
# CORREOS PARA PROFESORES
# ==========================================================

# Mensaje automatico tras hacer el registro
# Mensaje automático tras hacer el registro (Estructura Original Mantenida)
def enviar_correo_recepcion_profesor(profesor, dominio):
    msg = MIMEMultipart('alternative')
    msg['From'] = f"Recursos Humanos UNGE <{CORREO_MATRICULAS_USER}>"
    # Usamos el correo personal que el aspirante acaba de registrar
    msg['To'] = profesor.correo_personal
    msg['Subject'] = f"Solicitud de Registro Recibida - Ref: {profesor.id}"

    html_content = f"""
    <html>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7f9;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse; background-color: #ffffff; margin-top: 30px; border-radius: 15px; border: 1px solid #e1e8ed; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <tr>
                <td align="center" style="padding: 40px 0 20px 0; background-color: #ffffff;">
                    <h1 style="margin: 0; font-size: 14px; color: #1a237e; letter-spacing: 1px; text-transform: uppercase;">Universidad Nacional de Guinea Ecuatorial</h1>
                    <p style="margin: 5px 0 0 0; font-size: 16px; color: #1a237e; font-weight: bold;">Departamento de Recursos Humanos</p>
                </td>
            </tr>
            <tr>
                <td style="padding: 20px 40px; text-align: center; background-color: #ff6f00;">
                    <h2 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 300;">SOLICITUD EN REVISIÓN</h2>
                </td>
            </tr>
            <tr>
                <td style="padding: 40px 40px 20px 40px;">
                    <p style="font-size: 18px; color: #2c3e50; margin-bottom: 25px;">Estimado/a Prof. <strong>{profesor.nombre_aspirante} {profesor.apellidos_aspirante}</strong>,</p>
                    <p style="font-size: 15px; color: #546e7a; line-height: 1.6; margin-bottom: 25px;">
                        Le informamos que hemos recibido satisfactoriamente su solicitud de registro y la documentación adjunta (DIP y Credenciales). 
                        Actualmente, nuestro equipo está verificando la autenticidad de los datos.
                    </p>
                    <div style="background-color: #f8fafb; border-radius: 10px; padding: 25px; border-left: 5px solid #1a237e; margin-bottom: 30px;">
                        <table width="100%" style="font-size: 14px; color: #37474f;">
                            <tr><td><strong>ID DE SOLICITUD:</strong></td><td style="text-align: right;">#{profesor.id}</td></tr>
                            <tr><td><strong>DIP:</strong></td><td style="text-align: right;">{profesor.dip_aspirante}</td></tr>
                            <tr><td><strong>DEPARTAMENTO:</strong></td><td style="text-align: right;">{profesor.departamento}</td></tr>
                        </table>
                    </div>
                    <p style="font-size: 14px; color: #455a64; text-align: center;">
                        Una vez aprobada su solicitud, recibirá un segundo correo con su <strong>cuenta institucional</strong> y su <strong>código de activación</strong>.
                    </p>
                </td>
            </tr>
            <tr>
                <td style="background-color: #eceff1; padding: 30px; text-align: center;">
                    <p style="margin: 0; color: #78909c; font-size: 12px;"><strong>UNGE - Gestión de Profesorado</strong><br>Este es un mensaje automático.</p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html'))

    # BLOQUE DE ENVÍO CONFIGURADO PARA MAILHOG
    try:
        with smtplib.SMTP('127.0.0.1', 1025) as server:
            server.send_message(msg)
            print(f"DEBUG: Correo de recepción enviado a {profesor.correo_personal}")
    except Exception as e:
        print(f"DEBUG ERROR: No se pudo enviar el correo: {e}")


# Correo de activacion de la cuenta
# Correo de activacion de la cuenta (Estructura Original Mantenida)
def enviar_activacion_profesor(aspirante, codigo, correo_inst, dominio):
    msg = MIMEMultipart('alternative')
    msg['From'] = f"Soporte Técnico UNGE <{CORREO_MATRICULAS_USER}>"
    # IMPORTANTE: Se envía al correo personal para que pueda verlo y activar
    msg['To'] = aspirante.correo_personal
    msg['Subject'] = "¡ALTA CONFIRMADA! Active su Cuenta de Docente"

    # Ajustamos la URL para que coincida con nuestra nueva estructura limpia
    url_activacion = f"{dominio.rstrip('/')}/profesor/activar"

    html_content = f"""
    <html>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7f9;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse; background-color: #ffffff; margin-top: 30px; border-radius: 15px; border: 1px solid #e1e8ed; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <tr>
                <td align="center" style="padding: 40px 0 20px 0; background-color: #ffffff;">
                    <h1 style="margin: 0; font-size: 14px; color: #1a237e; letter-spacing: 1px; text-transform: uppercase;">Universidad Nacional de Guinea Ecuatorial</h1>
                    <p style="margin: 5px 0 0 0; font-size: 16px; color: #28a745; font-weight: bold;">Validación de Identidad Docente</p>
                </td>
            </tr>
            <tr>
                <td style="padding: 20px 40px; text-align: center; background-color: #1a237e;">
                    <h2 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 300;">¡CUENTA VALIDADA!</h2>
                </td>
            </tr>
            <tr>
                <td style="padding: 40px 40px 20px 40px;">
                    <p style="font-size: 18px; color: #2c3e50; margin-bottom: 25px;">Estimado/a <strong>{aspirante.nombre_aspirante}</strong>,</p>
                    <p style="font-size: 15px; color: #546e7a; line-height: 1.6;">Su identidad ha sido confirmada. Se ha generado su nueva identidad digital para el acceso a la plataforma académica:</p>
                    
                    <div style="background-color: #f8fafb; border-radius: 10px; padding: 25px; border-left: 5px solid #28a745; margin: 25px 0;">
                        <p style="margin: 0; font-size: 13px;"><strong>CORREO INSTITUCIONAL:</strong></p>
                        <p style="font-size: 18px; color: #1a237e; font-weight: bold; margin: 5px 0;">{correo_inst}</p>
                        <p style="margin: 15px 0 0 0; font-size: 13px;"><strong>CÓDIGO DE ACTIVACIÓN:</strong></p>
                        <p style="font-size: 22px; color: #ff6f00; font-weight: bold; letter-spacing: 4px; margin: 5px 0;">{codigo}</p>
                    </div>

                    <div style="text-align: center; margin: 40px 0;">
                        <a href="{url_activacion}" 
                           style="background-color: #1a237e; color: #ffffff; padding: 18px 35px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                            ACTIVAR MI CUENTA DOCENTE
                        </a>
                    </div>
                </td>
            </tr>
            <tr>
                <td style="background-color: #eceff1; padding: 30px; text-align: center;">
                    <p style="margin: 0; color: #78909c; font-size: 11px;">Este código es de un solo uso. Si no reconoce esta solicitud, contacte con soporte técnico.</p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html'))

    # BLOQUE DE ENVÍO SMTP (Mantenemos MailHog)
    try:
        with smtplib.SMTP('127.0.0.1', 1025) as server:
            server.send_message(msg)
            print(f"DEBUG: Correo de activación enviado a {aspirante.correo_personal}")
    except Exception as e:
        print(f"DEBUG ERROR: No se pudo enviar el correo de activación: {e}")


# REGISTRO RECHAZADO
def enviar_rechazo_profesor(usuario, motivo, dominio):
    msg = MIMEMultipart('alternative')
    msg['From'] = f"Recursos Humanos UNGE <{CORREO_MATRICULAS_USER}>"
    msg['To'] = usuario.correo
    msg['Subject'] = "IMPORTANTE: Solicitud de Registro Denegada"

    # Ajustamos el enlace para que el profesor pueda volver a intentarlo 
    # en la ruta correcta que configuramos antes
    url_reintento = f"{dominio.rstrip('/')}/profesor/registro"

    html_content = f"""
    <html>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7f9;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse; background-color: #ffffff; margin-top: 30px; border-radius: 15px; border: 1px solid #e1e8ed; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <tr>
                <td align="center" style="padding: 40px 0 20px 0; background-color: #ffffff;">
                    <h1 style="margin: 0; font-size: 14px; color: #b71c1c; letter-spacing: 1px; text-transform: uppercase;">Universidad Nacional de Guinea Ecuatorial</h1>
                    <p style="margin: 5px 0 0 0; font-size: 16px; color: #b71c1c; font-weight: bold;">Departamento de Recursos Humanos</p>
                </td>
            </tr>
            <tr>
                <td style="padding: 20px 40px; text-align: center; background-color: #b71c1c;">
                    <h2 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 300;">SOLICITUD RECHAZADA</h2>
                </td>
            </tr>
            <tr>
                <td style="padding: 40px 40px 20px 40px;">
                    <p style="font-size: 18px; color: #2c3e50; margin-bottom: 25px;">Estimado/a <strong>{usuario.nombre}</strong>,</p>
                    <p style="font-size: 15px; color: #546e7a; line-height: 1.6;">
                        Tras revisar su documentación, lamentamos informarle que su solicitud de alta como docente ha sido <strong>RECHAZADA</strong> por el siguiente motivo:
                    </p>
                    
                    <div style="background-color: #fff5f5; border-radius: 10px; padding: 25px; border-left: 5px solid #b71c1c; margin: 25px 0; color: #b71c1c; font-weight: bold;">
                        {motivo}
                    </div>

                    <p style="font-size: 14px; color: #455a64;">
                        Para subsanar este error, deberá realizar un nuevo registro con la documentación correcta o ponerse en contacto con la secretaría académica.
                    </p>

                    <div style="text-align: center; margin: 40px 0;">
                        <a href="{url_reintento}" 
                           style="background-color: #2c3e50; color: #ffffff; padding: 18px 35px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                           INTENTAR REGISTRO DE NUEVO
                        </a>
                    </div>
                </td>
            </tr>
            <tr>
                <td style="background-color: #eceff1; padding: 30px; text-align: center;">
                    <p style="margin: 0; color: #78909c; font-size: 11px;">UNGE - Sistema de Gestión de Credenciales</p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html'))

    # BLOQUE DE ENVÍO SMTP
    try:
        with smtplib.SMTP('127.0.0.1', 1025) as server:
            server.send_message(msg)
            print(f"DEBUG: Correo de rechazo enviado a {usuario.correo}")
    except Exception as e:
        print(f"DEBUG ERROR: No se pudo enviar el correo de rechazo: {e}")




# ==========================================================
# SECCION PARA LA SECRETARIA
# ==========================================================

@app.route('/secretaria/panel')
@requiere_login
@requiere_rol('profesor') # Asumiendo que usas el rol profesor para ella
def panel_secretaria():
    # Obtenemos sus datos de perfil
    datos_secretaria = Profesor.query.filter_by(usuario_id=current_user.id).first()
    
    if not datos_secretaria:
        abort(404)
        
    return render_template('secretaria_panel.html', s=datos_secretaria)

# ==========================================================
# PANEL PARA DIRECTIVOS
# ==========================================================

# PANEL ADMINISTRATIVO
@app.route('/decano/panel')
@requiere_login
@requiere_rol('directivo') # Aquí usamos el rol directivo que definiste antes
def directivo_panel():
    # Datos del decano para mostrar en las credenciales
    datos_decano = Profesor.query.filter_by(usuario_id=current_user.id).first()
    return render_template('directivo_panel.html', d=datos_decano)

# VISTA DEL DIRECTIVO
@app.route('/perfil/directivo/<int:directivo_id>')
def ver_perfil_directivo(directivo_id):
    # Buscamos el directivo por su ID
    # .get_or_404() hace que si no existe, muestre una página de error limpia
    directivo = Directivo.query.get_or_404(directivo_id)
    
    # Renderizamos el perfil público (asegúrate de que el nombre del archivo coincida)
    return render_template('perfil_publico_decano.html', d=directivo)



# ==========================================================
# ADMINSTRACION GENERAL DE LA PLATAFORMA
# ==========================================================

# PANEL DEL ADMIN
@app.route('/panel_admin')
@login_required
@requiere_rol("admin")
def panel_admin():
    # Solo permitimos el acceso si el rol es 'admin' o 'administrador'
    if current_user.rol not in ['admin', 'administrador']:
        return "Acceso denegado", 403

    # Recolección de datos reales para el Dashboard
    total_est = Usuario.query.filter_by(rol='estudiante').count()
    total_prof = Usuario.query.filter_by(rol='profesor').count()
    total_direc = Usuario.query.filter_by(rol='directivo').count()
    total_admin = Usuario.query.filter_by(rol='admin').count()
    pendientes = 12  # Esto vendrá de tu tabla de inscripciones luego
    buzon = 5       # Esto vendrá de tu tabla de mensajes/dudas
    
    # Obtenemos los últimos 5 usuarios registrados para la tabla
    ultimos = Usuario.query.order_by(Usuario.fecha_creacion.desc()).limit(5).all()

    return render_template('admin_panel.html', 
                           total_estudiantes=total_est,
                           total_profesores=total_prof,
                           total_directivos=total_direc,
                           total_administradores=total_admin,
                           solicitudes_pendientes=pendientes,
                           dudas_buzon=buzon,
                           ultimos_usuarios=ultimos)


# SU RUTA PARA HACER LOGIN

@app.route('/admin/login', methods=['GET', 'POST'])
def login_admin():

    # Contamos cada tipo de usuario
    total_est = Usuario.query.filter_by(rol='estudiante').count()
    total_prof = Usuario.query.filter_by(rol='profesor').count()
    total_dir = Usuario.query.filter_by(rol='directivo').count()
    total_adm = Usuario.query.filter_by(rol='admin').count()

    # Otros datos (puedes dejarlos en 0 por ahora o contarlos si tienes las tablas)
    pendientes = 0 
    buzon = 0
    ultimos = Usuario.query.order_by(Usuario.id.desc()).limit(5).all()
    # Si ya está logueado como admin, enviarlo al panel
    if current_user.is_authenticated and current_user.rol == 'admin':
        return redirect(url_for('panel_admin'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Buscamos por correo o por un campo 'username' si lo tienes
        user = Usuario.query.filter_by(correo_institucional=username).first()

        if user and check_password_hash(user.password_hash, password):
            if user.rol == 'admin':
                login_user(user)
                return redirect(url_for('panel_admin'))
            else:
                flash('Acceso denegado: Esta terminal es solo para administradores.', 'danger')
        else:
            flash('Credenciales de administrador incorrectas.', 'danger')

    return render_template('login_admin.html')




# ==========================================================
# DIRECTORIO DE PROFESORES
# ==========================================================

# LISTAR PROFESORES
@app.route('/directorio/profesores')
@login_required
def directorio_profesores():
    # 1. Consulta unificada trayendo al Usuario y sus posibles perfiles adicionales
    docentes_raw = db.session.query(Usuario, Profesor, Directivo).outerjoin(
        Profesor, Usuario.id == Profesor.usuario_id
    ).outerjoin(
        Directivo, Usuario.id == Directivo.usuario_id
    ).filter(
        Usuario.rol.in_(['profesor', 'directivo', 'admin'])
    ).all()
    
    # 2. Extraer listas únicas para los filtros dinámicos del HTML
    # Filtramos valores None o vacíos para que el select se vea limpio
    departamentos_existentes = sorted(list(set([p.departamento for u, p, d in docentes_raw if p and p.departamento])))
    cargos_existentes = sorted(list(set([d.cargo for u, p, d in docentes_raw if d and d.cargo])))

    directorio = []
    
    for usuario, profe, directivo in docentes_raw:
        # LÓGICA DE FOTO:
        # Prioridad Directivo: tabla Usuario | Prioridad Profesor: tabla Profesor
        foto_final = None
        if usuario.rol == 'directivo':
            foto_final = usuario.foto_perfil
        elif usuario.rol == 'profesor' and profe:
            foto_final = profe.archivo_foto
        
        # Fallback general (si no hay foto en tabla Profesor, busca en Usuario)
        if not foto_final:
            foto_final = usuario.foto_perfil

        # Definir el subtítulo para que el filtro de JS tenga una cadena con qué comparar
        if usuario.rol == 'directivo' and directivo:
            subtitulo = directivo.cargo
        elif profe:
            subtitulo = profe.departamento
        else:
            subtitulo = usuario.rol.capitalize()

        directorio.append({
            'usuario': usuario,
            'profe': profe,
            'directivo': directivo,
            'foto_display': foto_final,
            'subtitulo': subtitulo
        })
    
    # 3. Enviamos el directorio y las listas de filtros al template
    return render_template(
        'directorio_profesores.html', 
        directorio=directorio, 
        departamentos=departamentos_existentes,
        cargos=cargos_existentes
    )

# ==========================================================
# DIRECTORIO DE ESTUDIANTES
# ==========================================================
@app.route('/directorio/estudiantes')
@login_required
def directorio_estudiantes():
    # Consultamos solo la tabla Usuario filtrando por el rol 'estudiante'
    estudiantes = Usuario.query.filter_by(rol='estudiante').all()
    
    # Extraer carreras únicas directamente de la columna carrera en usuarios
    carreras_existentes = sorted(list(set([u.carrera for u in estudiantes if u.carrera])))

    directorio = []
    for u in estudiantes:
        directorio.append({
            'usuario': u,
            'foto_display': u.foto_perfil,
            # Usamos los campos de la tabla usuarios para el subtítulo
            'subtitulo': f"{u.carrera or 'Estudiante'} - {u.curso or ''}"
        })
    
    return render_template(
        'directorio_estudiantes.html', 
        directorio=directorio, 
        carreras=carreras_existentes
    )


# ==========================================================
# BLOG DE NOTAS PARA ESTUDIANTES
# ==========================================================
@app.route('/notas')
@login_required
def ver_notas():
    # Obtenemos asignaturas (puedes filtrarlas por usuario si tu modelo lo permite)
    asignaturas = Asignatura.query.all()
    datos_completos = []

    for asig in asignaturas:
        # Obtenemos todas las notas de este usuario para esta asignatura
        notas_db = Nota.query.filter_by(asignatura_id=asig.id, usuario_id=current_user.id).all()
        
        # Inicializamos los 10 huecos vacíos para cada tipo
        cps = {i: "" for i in range(1, 11)}
        sms = {i: "" for i in range(1, 11)}
        evs = {i: "" for i in range(1, 11)}
        
        # Variable para guardar la reacción de la asignatura (tomamos la de la primera nota que encontremos)
        reaccion_actual = ""

        # Ubicamos cada nota en su posición exacta usando la columna 'posicion'
        for n in notas_db:
            if n.tipo == 'Práctica' and n.posicion:
                cps[n.posicion] = n.contenido
            elif n.tipo == 'Seminario' and n.posicion:
                sms[n.posicion] = n.contenido
            elif n.tipo == 'Evaluación' and n.posicion:
                evs[n.posicion] = n.contenido
            
            # Guardamos la reacción si existe
            if n.reaccion:
                reaccion_actual = n.reaccion

        datos_completos.append({
            'asignatura': asig,
            'cps': cps,
            'sms': sms,
            'evs': evs,
            'reaccion': reaccion_actual
        })
        
    return render_template('notas.html', tabla_datos=datos_completos)

# GUARDAR NOTAS INSERTADAS
@app.route('/guardar_matriz', methods=['POST'])
@login_required
def guardar_matriz():
    datos = request.get_json() 
    
    try:
        for item in datos:
            # 1. Buscar o crear la asignatura
            asig = Asignatura.query.filter_by(nombre=item['asignatura']).first()
            
            if not asig:
                # CREAR: Ahora 'creditos' existe en el modelo, funcionará bien
                asig = Asignatura(
                    nombre=item['asignatura'], 
                    creditos=int(item.get('creditos') or 0)
                )
                db.session.add(asig)
                db.session.flush()
            else:
                # ACTUALIZAR: Si la asignatura ya existe, actualizamos sus créditos
                asig.creditos = int(item.get('creditos') or 0)

            # 2. Limpiamos registros previos de notas para esta asignatura/usuario
            Nota.query.filter_by(asignatura_id=asig.id, usuario_id=current_user.id).delete()

            # 3. Procesar el array de 30 notas
            for i, valor in enumerate(item['notas']):
                # Guardamos si hay contenido o si hay una reacción
                if (valor and valor.strip() != "") or item.get('reaccion'):
                    if i < 10:
                        tipo_nota, pos = 'Práctica', i + 1
                    elif i < 20:
                        tipo_nota, pos = 'Seminario', (i - 10) + 1
                    else:
                        tipo_nota, pos = 'Evaluación', (i - 20) + 1

                    nueva_nota = Nota(
                        usuario_id=current_user.id,
                        asignatura_id=asig.id,
                        tipo=tipo_nota,
                        posicion=pos,
                        contenido=valor,
                        reaccion=item.get('reaccion')
                    )
                    db.session.add(nueva_nota)
        
        db.session.commit()
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"ERROR REAL DEL SERVIDOR: {str(e)}") 
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================================
# CONFIGURACIÓN DE FLASK-LOGIN (PROFESIONAL)
# ==========================================================
login_manager = LoginManager()
login_manager.init_app(app)

# Indicar la ruta del login (ajusta 'login_page' al nombre real de tu función)
login_manager.login_view = 'login_page' 
login_manager.login_message = "Por favor, inicia sesión para acceder."
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    # Flask-Login usará esta función para cargar al usuario en 'current_user'
    print(f"DEBUG: Cargando usuario ID {user_id}") # Esto saldrá en tu terminal
    return Usuario.query.get(int(user_id))




# ==========================================================
# INICIAR SERVIDOR
# ==========================================================
with app.app_context():
    # db.create_all()
    pass
    

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)

