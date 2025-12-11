import os
# from msilib.schema import File
from dotenv import load_dotenv
from datetime import datetime, date
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix

from flask import (
    Flask, jsonify, request, redirect, url_for, send_file,
    render_template, send_file, session, abort, flash
)

from docx import Document
import io
import bleach
import uuid

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_cors import CORS

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, FileField, SubmitField


from forms import (
    NoticiaForm, PerfilForm, CambiarContrasenaForm, FileAllowed_PERFILES_EXIT, Email, EqualTo, DataRequired, 
    Length, Optional, ValidationError, PasswordField, DebateForm, BibliotecaForm, LibroFisicoForm
    )

from models import (
    db, Usuario, Estudiante, Nota, Mensaje, Calendario, Evento, Debate, Notificacion, Administrador, Comentario,
    Matricula, CodigoEstudiante, Asignatura, EstudianteAsignatura, Noticia, Debate, Notificacion, Comentario,
    Biblioteca

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

# Indica a Flask que confíe en los proxies (necesario en Render/servidores en la nube)
app.config['PREFERRED_URL_SCHEME'] = 'https'
#Forzar que la cookie de sesión solo se envíe sobre HTTPS, esto resuelve el problema de la sesión en el navegador de Render
app.config['SESSION_COOKIE_SECURE'] = True

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
#-----------------------------------------

# Aranciar la abse de datos
db.init_app(app)
CORS(app)

# Mirgraciones
migrate = Migrate(app, db)


# ===== INYECTAR VARIABLES GLOBALES EN TODOS LOS TEMPLATES (ANTES DE CUALQUIER RUTA) =====
@app.context_processor
def inyectar_contexto():
    """Inyecta logueado, usuario, rol, usuario_id en TODOS los templates automáticamente"""
    return {
        'logueado': 'usuario_id' in session,
        'usuario': session.get('nombre', ''),
        'rol': session.get('rol', ''),
        'usuario_id': session.get('usuario_id')
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
def requiere_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return wrapper

def requiere_rol(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'rol' not in session or session['rol'] not in roles:
                return abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ==========================================================
# RUTAS PÚBLICAS
# ==========================================================
@app.route('/')
def inicio():
    noticias = Noticia.query.order_by(Noticia.fecha.desc()).limit(9).all()
    return render_template('index.html', noticias=noticias)

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/registro')
def registro_page():
    return render_template('registro.html')

@app.route("/noticias")
def noticias_page():
    noticias = Noticia.query.order_by(Noticia.fecha.desc()).all()
    return render_template("lista_noticia.html", noticias=noticias)

@app.route('/contacto')
def contacto_page():
    return render_template('contacto.html')

@app.route('/notas')
def notas_page():
    return render_template('notas.html')

@app.route('/expedientes')
def expedientes_page():
    return render_template('expedientes.html')

@app.route('/asignaturas')
def asignaturas_page():
    return render_template('asignaturas.html')

@app.route('/calendario')
def calendario_page():
    return render_template('calendario.html')

@app.route('/eventos')
def eventos_page():
    return render_template('eventos.html')

@app.route('/mensajes')
def mensajes_page():
    return render_template('mensajes.html')

@app.route('/perfil')
def perfil_page():
    if 'usuario_id' not in session:
        flash("Debes iniciar sesión", "warning")
        return redirect(url_for('login_page'))
    return redirect(url_for('ver_perfil', usuario_id=session['usuario_id']))

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
    """Autenticación: espera JSON { correo, clave } (compatible con frontend)"""
    if not request.is_json:
        return jsonify({'mensaje': 'Se requiere JSON'}), 400

    data = request.get_json()
    correo = (data.get('correo') or '').strip().lower()
    clave = data.get('clave') or data.get('password') or ''
    usuario = Usuario.query.filter_by(correo=correo).first()
    if not usuario:
        return jsonify({'ok': False, 'mensaje': 'Usuario no encontrado'}), 404

    # En modelo guardamos password_hash; comprobar con check_password_hash
    if not check_password_hash(getattr(usuario, 'password_hash', ''), clave):
        return jsonify({'ok': False, 'mensaje': 'Credenciales incorrectas'}), 401

    # Guardar sesión
    session['usuario_id'] = usuario.id
    session['nombre'] = usuario.nombre
    session['rol'] = usuario.rol

    return jsonify({
        'ok': True,
        'mensaje': 'Login correcto',
        'usuario': {'id': usuario.id, 'nombre': usuario.nombre, 'rol': usuario.rol}
    }), 200

@app.route('/api/usuario_sesion', methods=['GET'])
def usuario_sesion():
    if 'usuario_id' not in session:
        return jsonify({'logueado': False})
    return jsonify({
        'logueado': True,
        'id': session['usuario_id'],
        'nombre': session['nombre'],
        'rol': session['rol']
    })

# ==========================================================
# SISTEMA DE MATRÍCULA
# ==========================================================
@app.route('/api/matricula', methods=['POST'])
def api_matricula():
    data = request.get_json()
    nombre = data.get('nombre', '').strip()
    correo = data.get('correo', '').strip().lower()
    carrera = data.get('carrera', '').strip()

    if not (nombre and correo and carrera):
        return jsonify({'ok': False, 'msg': 'Faltan campos'}), 400

    nueva = Matricula(nombre=nombre, correo=correo, carrera=carrera)
    db.session.add(nueva)
    db.session.commit()

    codigo = f"STD-{nueva.id:05d}"
    nuevo_codigo = CodigoEstudiante(codigo=codigo, correo=correo, usado=False)
    db.session.add(nuevo_codigo)
    db.session.commit()

    return jsonify({'ok': True, 'codigo': codigo})

@app.route('/api/registro', methods=['POST'])
def api_registro():
    """Registro: espera JSON { nombre, correo, clave, codigo_estudiante }"""
    if not request.is_json:
        return jsonify({'ok': False, 'msg': 'Se requiere JSON'}), 400

    data = request.get_json()
    nombre = (data.get('nombre') or '').strip()
    correo = (data.get('correo') or '').strip().lower()
    clave = data.get('clave') or data.get('password') or ''
    codigo = data.get('codigo_estudiante')

    if not (nombre and correo and clave and codigo):
        return jsonify({'ok': False, 'msg': 'Faltan campos'}), 400

    codigo_obj = CodigoEstudiante.query.filter_by(codigo=codigo, correo=correo, usado=False).first()
    if not codigo_obj:
        return jsonify({'ok': False, 'msg': 'Código inválido o ya usado'}), 400

    nuevo = Usuario(
        nombre=nombre,
        correo=correo,
        password_hash=generate_password_hash(clave),
        rol="estudiante"
    )
    db.session.add(nuevo)
    db.session.commit()

    matricula = Matricula.query.filter_by(correo=correo).first()
    estudiante = Estudiante(
        usuario_id=nuevo.id,
        matricula=f"M-{matricula.id:05d}" if matricula else f"M-{nuevo.id:05d}",
        carrera=getattr(matricula, 'carrera', 'Sin asignar')
    )
    db.session.add(estudiante)

    codigo_obj.usado = True
    db.session.commit()

    return jsonify({'ok': True, 'msg': 'Usuario registrado', 'usuario_id': nuevo.id}), 201

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

    inscripcion = EstudianteAsignatura(
        estudiante_id=estudiante.id,
        asignatura_id=asignatura_id
    )
    db.session.add(inscripcion)
    db.session.commit()

    return jsonify({'ok': True, 'msg': 'Inscripción exitosa'})


# ==========================================================
# BUZÓN DE CONTACTO
# ==========================================================
@app.route('/buzon', methods=['POST'])
def buzon():
    """
    Recibe el form multipart/form-data desde index.html (contacto/buzón).
    Guarda archivo opcional en UPLOAD_DIR y escribe entrada en mensajes.log.
    Redirige a inicio.
    """
    nombre = request.form.get('nombre', '').strip()
    correo = request.form.get('correo', '').strip()
    mensaje = request.form.get('mensaje', '').strip()
    archivo = request.files.get('archivo')

    archivo_nombre = None
    if archivo and archivo.filename:
        if not allowed_file(archivo.filename):
            return "Tipo de archivo no permitido", 400
        filename = secure_filename(archivo.filename)
        dest = os.path.join(UPLOAD_DIR, filename)
        # evitar sobreescritura
        if os.path.exists(dest):
            import time
            filename = f"{int(time.time())}_{filename}"
            dest = os.path.join(UPLOAD_DIR, filename)
        archivo.save(dest)
        archivo_nombre = filename

    # Guardar una entrada simple en log (no depende del modelo DB)
    try:
        logf = os.path.join(UPLOAD_DIR, 'mensajes.log')
        with open(logf, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.datetime.utcnow().isoformat()} | {nombre} | {correo} | {mensaje} | {archivo_nombre}\n")
    except Exception:
        pass

    return redirect(url_for('inicio'))


# ==========================================================
# CERRAR SESION
# ==========================================================
@app.route('/logout')
def logout():
    """Cierra la sesión del usuario y redirige a inicio"""
    session.clear()
    resp = redirect(url_for('inicio'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp



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
        nuevo = Mensaje(
            emisor_id=emisor_id,
            receptor_id=receptor_id,
            contenido=contenido
        )
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
        dest = os.path.join(UPLOAD_DIR, filename)
        # evitar sobreescritura
        if os.path.exists(dest):
            import time
            filename = f"{int(time.time())}_{filename}"
            dest = os.path.join(UPLOAD_DIR, filename)
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
@app.route('/api/eventos', methods=['GET'])
def listar_eventos():
    """Retorna todos los eventos del calendario"""
    from models import Calendario
    try:
        eventos = Calendario.query.order_by(Calendario.fecha.asc()).all()
        return jsonify([
            {
                'id': e.id,
                'title': e.titulo,
                'date': e.fecha.isoformat() if e.fecha else '',
                'description': e.descripcion or ''
            }
            for e in eventos
        ])
    except Exception as err:
        print(f'Error al listar eventos: {err}')
        return jsonify({'ok': False, 'msg': 'Error al cargar eventos'}), 500

@app.route('/api/eventos', methods=['POST'])
def agregar_evento():
    """Agregar evento (solo profesores/directivos)"""
    rol = session.get('rol')
    if rol not in ['profesor', 'directivo']:
        return jsonify({'ok': False, 'msg': 'No tienes permisos'}), 403

    data = request.get_json()
    from models import Calendario
    import datetime
    try:
        fecha_str = data.get('fecha', '')
        hora_str = data.get('hora', '')
        descripcion = data.get('descripcion', '').strip()
        creador_id = session.get('usuario_id')  # Asegúrate de que el ID del usuario esté en la sesión

        # Validar formato
        fecha = datetime.datetime.strptime(fecha_str, '%Y-%m-%d').date()
        hora = datetime.datetime.strptime(hora_str, '%H:%M').time()

        evento = Calendario(
            titulo=descripcion,
            fecha=fecha,
            hora=hora,
            descripcion=descripcion,
            creado_por=creador_id  # Asignar el ID del creador
        )
        db.session.add(evento)
        db.session.commit()

        return jsonify({'ok': True, 'msg': 'Evento agregado correctamente', 'evento_id': evento.id}), 201
    except ValueError as ve:
        print(f'Error de validación: {ve}')
        return jsonify({'ok': False, 'msg': 'Formato de fecha/hora inválido'}), 400
    except Exception as e:
        print(f'Error al agregar evento: {e}')
        db.session.rollback()
        return jsonify({'ok': False, 'msg': 'Error al agregar evento'}), 500

@app.route('/api/eventos/<int:evento_id>', methods=['DELETE'])
def eliminar_evento(evento_id):
    """Eliminar evento (solo profesores/directivos)"""
    rol = session.get('rol')
    if rol not in ['profesor', 'directivo']:
        return jsonify({'ok': False, 'msg': 'No tienes permisos'}), 403

    from models import Calendario
    try:
        evento = Calendario.query.get(evento_id)
        if not evento:
            return jsonify({'ok': False, 'msg': 'Evento no encontrado'}), 404

        db.session.delete(evento)
        db.session.commit()
        return jsonify({'ok': True, 'msg': 'Evento eliminado'})
    except Exception as e:
        print(f'Error al eliminar evento: {e}')
        db.session.rollback()
        return jsonify({'ok': False, 'msg': 'Error al eliminar evento'}), 500
    

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

# Metodo para guardar un PDF
def save_pdf_file(f):
    if not f or getattr(f, 'filename', '') == '':
        return None
    filename = secure_filename(f.filename)
    ext = filename.rsplit('.', 1)[-1].lower()
    if ext != 'pdf':
        return None
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    f.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
    return unique_name

# Metodo para guardar portadas de los documentos
def save_portada_file(file):
    filename = secure_filename(file.filename)
    path = os.path.join(app.root_path, "static/uploads/portadas", filename)
    file.save(path)
    return filename


# Rutas que quieren login
@app.route('/biblioteca/fisicos')
@requiere_login
def biblioteca_fisicos():
    libros = Biblioteca.query.filter_by(tipo_libro='fisico').all()
    return render_template('libros_fisicos.html', libros_fisicos=libros)

@app.route('/biblioteca/digitales')
@requiere_login
def biblioteca_digitales():
    # Libros normales
    libros = Biblioteca.query.filter_by(tipo_libro='libro').all()

    # Obtenemos el filtro de titulación desde la URL
    filtro_titulacion = request.args.get('titulacion', None)

    # Query de TFG
    query_tfg = Biblioteca.query.filter_by(tipo_libro='tfg')

    if filtro_titulacion:
        query_tfg = query_tfg.filter_by(titulacion=filtro_titulacion)

    tfg_publicos = query_tfg.all()

    return render_template('libros_digitales.html', libros=libros, tfg_publicos=tfg_publicos, filtro_titulacion=filtro_titulacion)


# Eliminar un libro TFG
@app.route('/biblioteca/eliminar/<int:item_id>', methods=['POST'])
def biblioteca_eliminar(item_id):
    item = Biblioteca.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('biblioteca_digitales'))

# Eliminar un libro normal

# Agregar libro digital
@app.route('/biblioteca/editar', methods=['GET', 'POST'])
@app.route('/biblioteca/editar/<int:item_id>', methods=['GET', 'POST'])
@requiere_login
def biblioteca_editar(item_id=None):
    item = Biblioteca.query.get(item_id) if item_id else None
    form = BibliotecaForm(obj=item)

    if item:
        form.publico.data = bool(item.publico)

    if form.validate_on_submit():

        
        # GUARDAR PORTADA (foto miniatura)
    
        portada_file = form.portada.data
        portada_filename = None

        if portada_file and portada_file.filename != "":
            nombre_original = secure_filename(portada_file.filename)
            portada_filename = f"{uuid.uuid4().hex}_{nombre_original}"

            carpeta_portadas = os.path.join(app.root_path, "static/uploads/portadas")
            os.makedirs(carpeta_portadas, exist_ok=True)

            portada_file.save(os.path.join(carpeta_portadas, portada_filename))

        # PDF o LINK
        
        tipo = form.tipo.data
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

    
        # ACTUALIZAR O CREAR NUEVO
      
        if item:
            # EDITAR
            item.titulo = form.titulo.data
            item.descripcion = form.descripcion.data
            item.tipo = tipo
            item.enlace = enlace
            item.tipo_libro = form.tipo_libro.data
            item.publico = bool(form.publico.data)
            item.titulacion = form.titulacion.data if form.tipo_libro.data == "tfg" else None


            if filename:
                item.archivo = filename

            if portada_filename:
                item.portada = portada_filename

        else:
            # CREAR
            nuevo = Biblioteca(
                titulo=form.titulo.data,
                descripcion=form.descripcion.data,
                tipo=tipo,
                archivo=filename,
                enlace=enlace,
                tipo_libro=form.tipo_libro.data,
                publico=bool(form.publico.data),
                usuario_id=session['usuario_id'],
                portada=portada_filename,  # ✔️ SOLO STRING
                titulacion = form.titulacion.data if form.tipo_libro.data == "tfg" else None
            )
            db.session.add(nuevo)

        db.session.commit()
        flash("Elemento guardado correctamente.", "success")
        return redirect(url_for('biblioteca_page'))

    return render_template('biblioteca_editar.html', form=form, item=item)


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

    return render_template('agregar_libro_fisico.html', form=form)


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





# ==========================================================
# INICIAR SERVIDOR
# ==========================================================
with app.app_context():
    # db.create_all()
    pass
    

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)

