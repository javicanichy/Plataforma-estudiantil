// prematricula.js
import { fetchJSON, mostrarMensaje } from './helpers.js';

export function initPreMatricula($id) {
  const formMatricula = $id('form-matricula');
  const matriculaMensaje = $id('matricula-mensaje');
  if (!formMatricula) return;

  formMatricula.addEventListener('submit', async (e) => {
    e.preventDefault();
    mostrarMensaje(matriculaMensaje, '');

    const nombre = ($id('mat_nombre')?.value || '').trim();
    const correo = ($id('mat_correo')?.value || '').trim().toLowerCase();
    const carrera = ($id('mat_carrera')?.value || '').trim();

    if (!nombre || !correo || !carrera) {
      mostrarMensaje(matriculaMensaje, 'Nombre, correo y carrera son obligatorios', 'text-danger');
      return;
    }

    const { ok, data } = await fetchJSON('/api/matricula', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nombre, correo, carrera })
    });

    if (ok) {
      mostrarMensaje(matriculaMensaje, `Código generado: ${data.codigo}`, 'text-success');
      formMatricula.reset();
    } else {
      mostrarMensaje(matriculaMensaje, data?.msg || 'Error en la prematrícula', 'text-danger');
    }
  });
}
