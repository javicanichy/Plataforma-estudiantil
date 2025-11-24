// perfil.js — módulo de perfil
// ================================================

// perfil.js — carga datos del perfil y muestra acciones según rol
// perfil.js — carga datos del perfil y muestra acciones según rol
document.addEventListener('DOMContentLoaded', async () => {
  const $id = id => document.getElementById(id);
  const usuario_id = localStorage.getItem('usuario_id');
  const usuario_rol = localStorage.getItem('usuario_rol'); // 'estudiante', 'profesor', 'directivo'

  const nombreEl = $id('nombre');
  const edadEl = $id('edad');
  const ubicacionEl = $id('ubicacion');
  const bioEl = $id('bio');
  const fotoEl = $id('foto-perfil');
  const accionesEl = $id('perfil-acciones');

  // Función para mostrar acciones según rol
  if (accionesEl && (usuario_rol === 'profesor' || usuario_rol === 'directivo')) {
    const btn = document.createElement('a');
    btn.textContent = 'Crear noticia';
    btn.href = '/nueva_noticia'; // Página correcta
    btn.className = 'btn btn-primary mt-3';
    accionesEl.appendChild(btn);
  }

  // Función para cargar datos del usuario desde backend
  if (!usuario_id) {
    nombreEl.textContent = 'Invitado';
    bioEl.textContent = 'Inicia sesión para ver tu perfil completo.';
    return;
  }

  try {
    const res = await fetch(`/api/usuarios/${usuario_id}`);
    const data = await res.json();

    if (res.ok && data.usuario) {
      const u = data.usuario;
      nombreEl.textContent = u.nombre || 'Sin nombre';
      edadEl.textContent = u.edad || 'No especificado';
      ubicacionEl.textContent = u.ubicacion || 'No especificado';
      bioEl.textContent = u.bio || 'Sin descripción';
      fotoEl.src = u.foto || '/static/img/default-user.png';
    } else {
      console.warn('No se pudo cargar el perfil', data);
    }
  } catch (err) {
    console.error('Error cargando perfil:', err);
  }
});
