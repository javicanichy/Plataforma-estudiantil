# Plataforma Estudiantil - Facultad de Ciencias de la Salud (UNGE)
# Sistema de Gestión Académica integral desarrollado con Flask para automatizar y centralizar los procesos administrativos y educativos de la Facultad de Ciencias de la Salud de la Universidad Nacional de Guinea Ecuatorial (UNGE).

La plataforma cuenta con un control de acceso basado en roles (Multi-rol), permitiendo una experiencia personalizada y segura para administradores, profesores y estudiantes.

Características Principales:
Autenticación y Seguridad: Registro e inicio de sesión seguro con contraseñas encriptadas y manejo de sesiones.

Gestión Multi-rol:

Administrador: Control total de usuarios (profesores y alumnos), asignación de asignaturas, gestión de cursos y configuración general del sistema.

Profesor: Carga y modificación de calificaciones, publicación de contenido de clases y gestión de listados de asistencia por asignatura.

Estudiante: Consulta en tiempo real de su expediente académico, notas por periodo, descarga de recursos docentes y notificaciones institucionales.

Automatización de Comunicaciones: Integración de notificaciones automáticas vía correo electrónico institucional para eventos clave (altas de usuario, avisos importantes, etc.).

Tecnologías y Herramientas
Backend: Python 3.9.8, Flask (con extensiones como Flask-SQLAlchemy, Flask-Login, Flask-Mail)

Base de Datos: PostgreSQL (alojado en Supabase)

Frontend: HTML5, CSS3 (diseño modular y responsive), Jinja2 para renderizado de plantillas.

Despliegue y Hosting: Configurado para servicios en la nube como Render.

# Estructura del Repositorio
Plaintext
├── app/
│   ├── static/          # Estilos CSS, scripts JS y recursos visuales
│   ├── templates/       # Vistas HTML organizadas por roles (admin, prof, alumno)
│   ├── __init__.py      # Inicialización de la app Flask y sus extensiones
│   ├── models.py        # Modelos ORM (Usuarios, Notas, Asignaturas, Cursos)
│   └── routes.py        # Controladores de rutas, lógica de negocio y autenticación
├── migrations/          # Historial de migraciones de la base de datos
├── .env.example         # Plantilla para variables de entorno
├── config.py            # Configuraciones del sistema (Mail, BD, Secret Keys)
├── requirements.txt     # Listado de dependencias del proyecto
└── run.py               # Punto de entrada para arrancar el servidor
# Instalación y Configuración Local
Sigue estos pasos para levantar un entorno de desarrollo local:

1. Clonar el repositorio
Bash
git clone https://github.com/javicanichy/Plataforma-estudiantil.git
cd Plataforma-estudiantil
2. Crear y activar el entorno virtual
Bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/macOS:
source venv/bin/activate
3. Instalar las dependencias necesarias
Bash
pip install -r requirements.txt
4. Configurar las Variables de Entorno
Crea un archivo .env en la raíz del proyecto tomando como referencia el .env.example y rellena tus credenciales correspondientes:

Fragmento de código
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=tu_clave_secreta_para_sesiones
DATABASE_URL=postgresql://usuario:password@host:port/dbname
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=tu_correo_institucional@unge.gq
MAIL_PASSWORD=tu_contraseña_de_aplicación
5. Preparar la Base de Datos
Si estás utilizando Flask-Migrate para el control de versiones de la base de datos, ejecuta:

Bash
flask db upgrade
6. Ejecutar la Aplicación
Arranca el servidor local de Flask:

Bash
flask run
Abre tu navegador e ingresa a [http://127.0.0.1:5000/](http://127.0.0.1:5000/).

# Despliegue en Producción
El proyecto está preparado para desplegarse fácilmente en plataformas como Render. Asegúrate de mapear correctamente las variables de entorno de tu archivo .env en el panel de configuración de tu Web Service y conectar la base de datos de producción (Supabase).

📄 Licencia e Institución
Este software es de carácter educativo e institucional, desarrollado específicamente para la optimización de los procesos internos de la Facultad de Ciencias de la Salud - UNGE.

Desarrollado y mantenido por Javicanichy.
