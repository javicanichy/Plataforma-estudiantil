// sesion.js
import { fetchJSON } from './helpers.js';

export async function actualizarSesion() {
  let usuario = { logueado: false };
  try {
    const res = await fetchJSON('/api/usuario_sesion');
    if (res.ok && res.data) usuario = res.data;
  } catch (err) {
    console.error("Error al obtener sesión:", err);
  }

  const contenedor = document.querySelector('.text-center.my-4');
  if (contenedor) {
    if (usuario.logueado) {
      contenedor.innerHTML = `
        <a href="/perfil" class="btn btn-success me-2">Ver mi perfil</a>
        <a href="/notas" class="btn btn-primary me-2">Ver mis notas</a>
        <a href="/mensajes" class="btn btn-warning me-2">Mensajes</a>
        <a href="/logout" class="btn btn-danger">Cerrar sesión</a>
      `;
    } else {
      contenedor.innerHTML = `<a href="/login" class="btn btn-outline-primary">Iniciar sesión</a>`;
    }
  }

  return usuario;
}
