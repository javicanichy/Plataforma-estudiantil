// registro.js
import { fetchJSON, mostrarMensaje } from './helpers.js';

export function initRegistro($id) {
  const formRegistro = $id('form-registro');
  const registroMensaje = $id('registro-mensaje');
  if (!formRegistro) return;

  formRegistro.addEventListener('submit', async (e) => {
    e.preventDefault();
    mostrarMensaje(registroMensaje, '');

    const nombre = ($id('nombre')?.value || '').trim();
    const correo = ($id('correo')?.value || '').trim().toLowerCase();
    const clave = $id('clave')?.value || '';
    const codigo_estudiante = ($id('codigo_estudiante')?.value || '').trim();

    if (!nombre || !correo || !clave || !codigo_estudiante) {
      mostrarMensaje(registroMensaje, 'Todos los campos son obligatorios', 'text-danger');
      return;
    }

    const { ok, data } = await fetchJSON('/api/registro', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nombre, correo, clave, codigo_estudiante })
    });

    if (ok) {
      mostrarMensaje(registroMensaje, data?.msg || 'Registro correcto', 'text-success');
      formRegistro.reset();
    } else {
      mostrarMensaje(registroMensaje, data?.msg || 'Error al registrar', 'text-danger');
    }
  });
}
