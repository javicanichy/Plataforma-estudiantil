// login.js

if (!window.__login_handler_init__) {
  window.__login_handler_init__ = true;

  document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('form-login');
    const msgDiv = document.getElementById('login-mensaje');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      msgDiv.textContent = '';
      msgDiv.className = 'mb-3 text-center text-danger';

      const correo = document.getElementById('correo').value.trim();
      const clave = document.getElementById('clave').value;

      // Validación básica
      if (!correo || !clave) {
        msgDiv.textContent = 'Completa todos los campos.';
        form.classList.add('was-validated');
        return;
      }

      try {
        const res = await fetch('/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ correo, clave })
        });

        const data = await res.json().catch(() => ({}));

        if (res.ok) {
          // Si login correcto, guardar id de usuario (opcional) y redirigir
          const usuario = data.usuario || data.user || null;
          if (usuario && usuario.id) {
            try {
              localStorage.setItem('usuario_id', usuario.id);
              localStorage.setItem('usuario_rol', usuario.rol || 'estudiante');
            } catch (err) {
              console.warn('No se pudo guardar en localStorage:', err);
            }
          }
          // Redirigir al dashboard
          msgDiv.textContent = 'Iniciando sesión...';
          msgDiv.className = 'mb-3 text-center text-success';
          setTimeout(() => {
            window.location.href = '/';
          }, 800);
        } else {
          // Error desde el servidor
          const msg = data.mensaje || data.error || 'Credenciales incorrectas';
          msgDiv.textContent = msg;
          msgDiv.className = 'mb-3 text-center text-danger';
        }
      } catch (err) {
        console.error('Error en petición POST /login:', err);
        msgDiv.textContent = 'Error de red. Intenta más tarde.';
        msgDiv.className = 'mb-3 text-center text-danger';
      }

      // Añadir autor_id al formData si es necesario
      const autor_id = localStorage.getItem('usuario_id');
      if (!autor_id) {
        alert("Error: No se ha identificado al usuario. Vuelve a iniciar sesión.");
        return;
                }
      formData.append("autor_id", autor_id);

    });
  });
}