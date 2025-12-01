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


  // ===========================
  // 1️⃣ VISTA PREVIA EN EL FORMULARIO
  // ===========================
  const fotoPortadaInput = document.getElementById('foto_portada_input');
  const previewContainer = document.getElementById('portada-slide-preview');
  let intervalPreviewID;
  let allFiles = []; // guardamos todas las fotos seleccionadas

  if (fotoPortadaInput && previewContainer) {
    fotoPortadaInput.addEventListener('change', function(event) {
        const files = Array.from(event.target.files);
        allFiles = allFiles.concat(files).slice(0, 3); // máximo 3 fotos

        // Limpiar previews anteriores
        previewContainer.innerHTML = '';
        const previews = [];
        let index = 0;

        allFiles.forEach(file => {
          const reader = new FileReader();
          reader.onload = function(e) {
            const img = document.createElement('img');
            img.src = e.target.result;
            img.classList.add('portada-slide-preview');
            img.style.display = 'inline-block'; // todas visibles
            previewContainer.appendChild(img);
          };
          reader.readAsDataURL(file);
        });


        // Carrusel interno de preview
        if (intervalPreviewID) clearInterval(intervalPreviewID);
        if (previews.length > 1) {
            intervalPreviewID = setInterval(() => {
                previews.forEach(img => img.style.display = 'none');
                previews[index].style.display = 'block';
                index = (index + 1) % previews.length;
            }, 1000); // cambia cada 1s en el preview
        }
    });

    // ===========================
    // 2️⃣ REEMPLAZAR FILES ANTES DE ENVIAR FORMULARIO
    // ===========================
    const form = fotoPortadaInput.closest('form');
    form.addEventListener('submit', function(event) {
        const dataTransfer = new DataTransfer();
        allFiles.forEach(file => dataTransfer.items.add(file));
        fotoPortadaInput.files = dataTransfer.files; // ahora se envían todas las fotos
    });
  }

  // ===========================
  // 3️⃣ CARRUSEL EN EL PERFIL
  // ===========================
  const slides = document.querySelectorAll('.portada-slide');
  console.log(slides); // aquí ya debería mostrar 3

  if (slides.length > 0) {
      let index = 0;
      slides.forEach((img, i) => {
          img.style.display = (i === 0) ? 'block' : 'none';
          img.style.position = 'absolute';
          img.style.top = '0';
          img.style.left = '0';
          img.style.width = '100%';
          img.style.height = '100%';
          img.style.objectFit = 'cover';
      });

      if (slides.length > 1) {
          setInterval(() => {
              slides[index].style.display = 'none';
              index = (index + 1) % slides.length;
              slides[index].style.display = 'block';
          }, 1000); // cambia cada 1 segundos
      }
  }


});
