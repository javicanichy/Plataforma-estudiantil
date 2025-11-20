// mensajes.js
import { fetchJSON, mostrarMensaje } from './helpers.js';

export function initMensajes($id) {
  const path = window.location.pathname;
  if (!path.includes('/mensajes')) return;

  const listaConversaciones = $id('lista-conversaciones');
  const chatContainer = $id('chat-container');
  const formMensaje = $id('form-mensaje');
  const mensajeInfo = $id('mensaje-info');
  let currentReceptorId = null;

  // Funciones: cargarConversaciones, cargarConversacion y envío de mensajes
  // Copia la lógica que ya tienes, usando fetchJSON y mostrarMensaje
  async function cargarConversaciones() { /* ... */ }
  async function cargarConversacion(id, nombre) { /* ... */ }

  if (formMensaje) {
    formMensaje.addEventListener('submit', async (e) => { /* ... */ });
  }

  cargarConversaciones();
}
