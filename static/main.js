// main.js — controla todas las interacciones del frontend
import { actualizarSesion } from './sesion.js';
import { initLogin } from './login.js';
import { initRegistro } from './registro.js';
import { initPreMatricula } from './prematricula.js';
import { initPerfil } from './perfil.js';
import { initNotas } from './notas.js';
import { initMensajes } from './mensajes.js';
import { initInscripcion } from './inscripcion.js';
import { initCalendario } from './calendario.js';


document.addEventListener('DOMContentLoaded', async () => {
  const $id = id => document.getElementById(id);
  let usuario = await actualizarSesion();

  // Inicialización de módulos
  initLogin($id);
  initRegistro($id);
  initPreMatricula($id);
  initPerfil($id);
  initNotas($id);
  initMensajes($id);
  initInscripcion($id);
  initCalendario($id);
});
