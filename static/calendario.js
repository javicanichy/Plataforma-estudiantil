document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Configuración de Seguridad y Elementos
    // usuarioRol debe venir definido en tu HTML (ej: const usuarioRol = "{{ current_user.rol }}";)
    const esEditor = (usuarioRol === 'directivo' || usuarioRol === 'admin');
    const eventModal = new bootstrap.Modal(document.getElementById('eventModal'));
    const saveEventBtn = document.getElementById('saveEventBtn');

    // 2. Reloj en tiempo real (Encabezado)
    function actualizarReloj() {
    const el = document.getElementById('reloj-digital');
    if (el) {
        const ahora = new Date();
        const texto = ahora.toLocaleString('es-ES', {
            weekday: 'long', day: 'numeric', month: 'long',
            hour: '2-digit', minute: '2-digit', second: '2-digit'
        });
        el.innerHTML = texto.toUpperCase();
        console.log("Reloj funcionando en pantalla");
    }
    }
    setInterval(actualizarReloj, 1000);
    window.addEventListener('load', actualizarReloj);

    // 3. Inicialización de FullCalendar
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        locale: 'es',
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,listWeek'
        },
        buttonText: {
            today: 'Hoy', month: 'Mes', week: 'Semana', list: 'Agenda'
        },
        
        // Permisos según Rol
        editable: esEditor,
        selectable: esEditor,
        selectMirror: true,
        dayMaxEvents: true,
        
        // Carga de eventos con truco para evitar caché (v=...)
        events: '/api/eventos?v=' + new Date().getTime(),

        // Pintar colores según el tipo de tu modelo
        eventDidMount: function(info) {
            const colors = {
                'importante': '#dc3545', // Rojo
                'general': '#0d6efd',    // Azul
                'divertido': '#ffc107'   // Amarillo
            };
            
            // Extrae el tipo del objeto que envía tu Python (to_dict)
            const tipo = info.event.extendedProps.tipo || 'general';
            
            info.el.style.backgroundColor = colors[tipo] || '#0dbd2a'; // Verde UNGE por defecto
            info.el.style.border = 'none';
            // Si es amarillo (divertido), ponemos letra negra para que se lea bien
            if (tipo === 'divertido') info.el.style.color = '#000';
        },

        // ACCIÓN: SELECCIONAR FECHAS (CREAR - Solo Editores)
        select: function(arg) {
            if (!esEditor) return;

            document.getElementById('eventForm').reset();
            document.getElementById('startStr').value = arg.startStr;
            document.getElementById('endStr').value = arg.endStr;
            document.getElementById('allDay').value = arg.allDay;
            
            eventModal.show();
        },

        // ACCIÓN: CLICK EN EVENTO (VER O ELIMINAR)
        eventClick: function(arg) {
            if (!esEditor) {
                // Estudiantes/Visitantes: Solo ven la información
                Swal.fire({
                    title: arg.event.title,
                    html: `<strong>Detalles:</strong><br>${arg.event.extendedProps.description || 'Sin descripción adicional.'}`,
                    icon: 'info',
                    confirmButtonColor: '#0dbd2a',
                    confirmButtonText: 'Cerrar'
                });
                return;
            }

            // Directivos/Admin: Pueden eliminar
            Swal.fire({
                title: '¿Eliminar evento?',
                text: `Vas a borrar: ${arg.event.title}`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    fetch(`/api/eventos/${arg.event.id}`, { method: 'DELETE' })
                    .then(response => {
                        if(response.ok) {
                            arg.event.remove();
                            Swal.fire('Eliminado', 'El evento ha sido borrado.', 'success');
                        } else {
                            Swal.fire('Error', 'No se pudo eliminar el evento.', 'error');
                        }
                    });
                }
            });
        }
    });

    // 4. Guardar Evento (Solo Editores)
    if (saveEventBtn) {
        saveEventBtn.addEventListener('click', function() {
            const title = document.getElementById('eventTitle').value;
            const description = document.getElementById('eventDescription').value; // Captura la descripción
            const tipo = document.getElementById('eventTipo').value;

            if (!title) {
                Swal.fire('Atención', 'Por favor, introduce un título', 'warning');
                return;
            }

            const data = {
                title: title,
                description: description, // Se envía a la columna 'descripcion'
                start: document.getElementById('startStr').value,
                end: document.getElementById('endStr').value,
                allDay: document.getElementById('allDay').value === 'true',
                tipo: tipo
            };

            fetch('/api/eventos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success || result.id) {
                    calendar.refetchEvents();
                    eventModal.hide();
                    Swal.fire('Guardado', 'El evento se ha creado con éxito', 'success');
                }
            })
            .catch(err => {
                console.error("Error al guardar:", err);
                Swal.fire('Error', 'Hubo un problema al conectar con el servidor', 'error');
            });
        });
    }

    calendar.render();
});



