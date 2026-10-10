document.addEventListener('DOMContentLoaded', function() {
  const calendarEl = document.getElementById('calendar');

  if (calendarEl) {
    const calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'dayGridMonth',
      locale: 'pt-br',
      
      headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek,timeGridDay'
      },

      events: [
        {
          title: 'Audiência de Conciliação',
          start: '2026-10-15',
          color: '#f89d81'
        },
        {
          title: 'Prazo: Contestação',
          start: '2026-10-20',
          color: '#fbd695'
        }
      ],

      dateClick: function(info) {
        alert('Dia clicado: ' + info.dateStr);
      },

      eventClick: function(info) {
        alert('Compromisso: ' + info.event.title);
      }
    });

    calendar.render();
  }
});

