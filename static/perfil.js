// perfil.js — módulo de perfil
// ================================================

export function initPerfil($id) {
  const fotoInput = $id('perfil-foto-input');
  const fotoImg = $id('perfil-foto-img');
  const nombreInput = $id('perfil-nombre');
  const guardarBtn = $id('perfil-guardar');
  const mensajeDiv = $id('perfil-mensaje');

  if (!fotoInput || !fotoImg || !nombreInput || !guardarBtn || !mensajeDiv) return;

  // 1️⃣ Cargar datos del usuario al iniciar
  fetch('/api/usuario_sesion')
    .then(res => res.json())
    .then(data => {
      if (data.logueado) {
        nombreInput.value = data.nombre || '';
        // Foto, si tienes endpoint para foto del usuario
        fotoImg.src = `/uploads/${data.foto || 'default.png'}`;
      }
    })
    .catch(err => console.error('Error cargando perfil:', err));

  // 2️⃣ Cambiar foto al seleccionar archivo
  fotoInput.addEventListener('change', () => {
    const file = fotoInput.files[0];
    if (!file) return;

    if (!['image/png','image/jpeg'].includes(file.type)) {
      mensajeDiv.textContent = 'Solo se permiten PNG o JPEG';
      return;
    }

    const reader = new FileReader();
    reader.onload = e => fotoImg.src = e.target.result;
    reader.readAsDataURL(file);
  });

  // 3️⃣ Guardar cambios
  guardarBtn.addEventListener('click', async () => {
    mensajeDiv.textContent = '';

    const formData = new FormData();
    formData.append('nombre', nombreInput.value);

    if (fotoInput.files[0]) {
      formData.append('foto', fotoInput.files[0]);
    }

    try {
      const res = await fetch('/api/actualizar_perfil', {
        method: 'POST',
        body: formData
      });
      const result = await res.json();
      if (result.ok) {
        mensajeDiv.textContent = 'Perfil actualizado correctamente ✅';
      } else {
        mensajeDiv.textContent = `Error: ${result.msg}`;
      }
    } catch (err) {
      console.error('Error actualizando perfil:', err);
      mensajeDiv.textContent = 'Error al actualizar perfil';
    }
  });
}
