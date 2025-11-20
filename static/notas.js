// notas.js
import { fetchJSON } from './helpers.js';

export function initNotas($id) {
  const path = window.location.pathname;
  if (!path.includes('/notas')) return;

  const listaNotas = $id('notas-list');
  if (!listaNotas) return;

  (async () => {
    listaNotas.innerHTML = '<li class="list-group-item">Cargando...</li>';
    try {
      const res = await fetchJSON('/api/usuario_sesion');
      if (!res.ok || !res.data?.logueado) {
        listaNotas.innerHTML = '<li class="list-group-item text-danger">No autenticado</li>';
        return;
      }

      const usuarioId = res.data.id;
      const r2 = await fetchJSON(`/api/notas/${usuarioId}`);
      if (!r2.ok || !Array.isArray(r2.data)) {
        listaNotas.innerHTML = '<li class="list-group-item">No hay notas.</li>';
        return;
      }

      listaNotas.innerHTML = '';
      r2.data.forEach(n => {
        const li = document.createElement('li');
        li.className = 'list-group-item';
        li.textContent = `${n.materia || n.asignatura || 'Asignatura'}: ${n.calificacion || n.nota || ''}`;
        listaNotas.appendChild(li);
      });
    } catch (err) {
      console.error(err);
      listaNotas.innerHTML = '<li class="list-group-item text-danger">Error al cargar notas</li>';
    }
  })();
}
