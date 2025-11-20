-- Crea las tablas según Backend/models.py (uso de SERIAL y DEFAULT now()).
-- Ejecutar en pgAdmin o: psql -h <host> -U <user> -d <dbname> -f create_tables.sql

-- Tabla usuarios
CREATE TABLE usuarios (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  correo VARCHAR(100) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  rol VARCHAR(20) NOT NULL,
  fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- Tabla profesores
CREATE TABLE profesores (
  id SERIAL PRIMARY KEY,
  usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  departamento VARCHAR(100) NOT NULL,
  fecha_ingreso TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- Tabla directivos
CREATE TABLE directivos (
  id SERIAL PRIMARY KEY,
  usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  cargo VARCHAR(100) NOT NULL,
  fecha_ingreso TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- Tabla estudiantes
CREATE TABLE estudiantes (
  id SERIAL PRIMARY KEY,
  usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  matricula VARCHAR(50) NOT NULL UNIQUE,
  carrera VARCHAR(100) NOT NULL,
  fecha_ingreso TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- Tabla asignaturas
CREATE TABLE asignaturas (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  codigo VARCHAR(50) NOT NULL UNIQUE,
  profesor_id INTEGER REFERENCES profesores(id) ON DELETE SET NULL
);

-- Tabla expedientes
CREATE TABLE expedientes (
  id SERIAL PRIMARY KEY,
  estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
  nombre_documento VARCHAR(200) NOT NULL,
  ruta_archivo TEXT NOT NULL,
  fecha_subida TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- Tabla notas
CREATE TABLE notas (
  id SERIAL PRIMARY KEY,
  estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
  asignatura VARCHAR(100) NOT NULL,
  nota DOUBLE PRECISION NOT NULL,
  fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- Tabla mensajes
CREATE TABLE mensajes (
  id SERIAL PRIMARY KEY,
  emisor_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
  receptor_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
  contenido TEXT NOT NULL,
  fecha TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  leido BOOLEAN DEFAULT FALSE NOT NULL
);

-- Índices recomendados
CREATE INDEX IF NOT EXISTS idx_usuarios_correo ON usuarios (correo);
CREATE INDEX IF NOT EXISTS idx_asignaturas_codigo ON asignaturas (codigo);
CREATE INDEX IF NOT EXISTS idx_notas_estudiante ON notas (estudiante_id);
CREATE INDEX IF NOT EXISTS idx_mensajes_receptor ON mensajes (receptor_id);