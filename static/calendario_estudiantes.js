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
    editable: true,
    dayMaxEvents: true,  // permite "más" cuando hay muchos eventos

    // ================= Eventos predefinidos =================
    events: [
      {
        title: 'Evento Todo el Día',
        start: '2025-01-01',
        classNames: ['evento-general']
      },
      {
        title: 'Evento Largo',
        start: '2025-01-07',
        end: '2025-01-10',
        classNames: ['evento-importante']
      },
      {
        groupId: 999,
        title: 'Evento Recurrente',
        start: '2025-01-09T16:00:00',
        classNames: ['evento-general']
      },
      {
        groupId: 999,
        title: 'Evento Recurrente',
        start: '2025-01-16T16:00:00',
        classNames: ['evento-general']
      },
      {
        title: 'Conferencia',
        start: '2025-01-11',
        end: '2025-01-13',
        classNames: ['evento-importante']
      },
      {
        title: 'Reunión',
        start: '2025-01-12T10:30:00',
        end: '2025-01-12T12:30:00',
        classNames: ['evento-general']
      },
      {
        title: 'Almuerzo',
        start: '2025-01-12T12:00:00',
        classNames: ['evento-general']
      },
      {
        title: 'Happy Hour',
        start: '2025-01-12T17:30:00',
        classNames: ['evento-divertido']
      },
      {
        title: 'Cena',
        start: '2025-01-12T20:00:00',
        classNames: ['evento-general']
      },
      {
        title: 'Fiesta de Cumpleaños',
        start: '2025-01-13T07:00:00',
        classNames: ['evento-divertido']
      },
      {
        title: 'Click para Google',
        url: 'http://google.com/',
        start: '2025-01-28',
        classNames: ['evento-general']
      }
    ],

    // ================= Agregar evento con prompt =================
    select: function(arg) {
      var title = prompt('Título del evento:');
      if (title) {
        var colorClase = prompt('Tipo de evento: "importante", "general" o "divertido"').toLowerCase();
        var className = 'evento-general';
        if(colorClase === 'importante') className = 'evento-importante';
        if(colorClase === 'divertido') className = 'evento-divertido';

        calendar.addEvent({
          title: title,
          start: arg.start,
          end: arg.end,
          allDay: arg.allDay,
          classNames: [className]
        });
      }
      calendar.unselect();
    },

    // ================= Click en evento =================
    eventClick: function(arg) {
      if (confirm('¿Seguro que deseas eliminar este evento?')) {
        arg.event.remove();
      }
    }

  });

  calendar.render();
});
