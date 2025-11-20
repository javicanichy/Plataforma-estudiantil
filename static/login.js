// login.js
import { fetchJSON, mostrarMensaje } from './helpers.js';
import { actualizarSesion } from './sesion.js';

export function initLogin($id) {
  const formLogin = $id('form-login');
  const loginMensaje = $id('login-mensaje');
  if (!formLogin) return;

  formLogin.addEventListener('submit', async (e) => {
    e.preventDefault();
    mostrarMensaje(loginMensaje, '');

    const correo = ($id('correo')?.value || '').trim();
    const clave = $id('clave')?.value || '';

    if (!correo || !clave) {
      mostrarMensaje(loginMensaje, 'Correo y contraseña son obligatorios', 'text-danger');
      return;
    }

    const { ok, data } = await fetchJSON('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ correo, clave })
    });

    if (ok) {
      await actualizarSesion();
      mostrarMensaje(loginMensaje, 'Login exitoso', 'text-success');
      formLogin.reset();
      setTimeout(() => window.location.href = '/', 350);
    } else {
      mostrarMensaje(loginMensaje, data?.mensaje || 'Error de inicio de sesión', 'text-danger');
    }
  });
}
