document.addEventListener('DOMContentLoaded', function() {
  
  // ================= RELOJ REAL =================
  function actualizarReloj() {
    const now = new Date();
    const formatted = now.toLocaleString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
    document.getElementById('calendar-title').textContent = formatted;
  }

  setInterval(actualizarReloj, 1000); // actualizar cada segundo
  actualizarReloj(); // inicializar


  // ================= CALENDARIO =================

  var calendarEl = document.getElementById('calendar');

  var calendar = new FullCalendar.Calendar(calendarEl, {
    locale: 'es', // idioma español
    height: 'auto',
    contentHeight: 'auto',
    expandRows: true,
    handleWindowResize: true,

    windowResize: function() {
      calendar.updateSize();
    },


    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay'
    },

// ================= Traducción de botones =================
  buttonText: {
    today: 'Hoy',
    month: 'Mes',
    week: 'Semana',
    day: 'Día',
    list: 'Agenda'
  },

    initialDate: new Date(),  // toma la fecha y hora actual del sistema
    navLinks: true,      // se puede hacer click en días/semanas
    selectable: true,
    selectMirror: true,
    editable: usuarioRol === 'directivo', // solo directivos pueden seleccionar
    dayMaxEvents: true,  // permite "más" cuando hay muchos eventos

    // ================= Eventos predefinidos =================
    events: '/api/eventos',

    // ================= Agregar evento con prompt =================
    select: function(arg) {
      if(usuarioRol !== 'directivo') return; // seguridad extra
      var title = prompt('Título del evento:');
      if (title) {
        var tipo = prompt('Tipo de evento: "importante", "general" o "divertido"').toLowerCase();
        if (!['importante', 'general', 'divertido'].includes(tipo)) {
          tipo = 'general';
        }

        // Agregar el nuevo evento al calendario y pasarlo al backend
        fetch('/api/eventos', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: title,
            start: arg.start.toISOString(),
            end: arg.end ? arg.end.toISOString() : null,
            allDay: arg.allDay,
            tipo: tipo
          })
        })
        .then(() => calendar.refetchEvents());
      }
    },

    // ================= Click en evento =================
    eventClick: function(arg) {
      if(usuarioRol !== 'directivo') return; // solo directivo puede eliminar
      if (confirm('¿Seguro que deseas eliminar este evento?')) {
        // Eliminar el evento del backend
        fetch(`/api/eventos/${arg.event.id}`, { method: 'DELETE' })
        .then(() => calendar.refetchEvents());
      }
    }

  });

  calendar.render();
});
