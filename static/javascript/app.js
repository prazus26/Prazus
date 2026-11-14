document.addEventListener('DOMContentLoaded', function () {

    const calendarEl = document.getElementById('calendar');

    if (!calendarEl) return;

    const calendar = new FullCalendar.Calendar(calendarEl, {

        initialView: 'dayGridMonth',
        locale: 'pt-br',
        height: 'auto',

        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },

        events: '/api/calendario/eventos',

        dateClick: function (info) {
            console.log('Dia selecionado:', info.dateStr);
        },

        eventClick: function (info) {
            info.jsEvent.preventDefault();

            const props = info.event.extendedProps;

            if (props.prazo_id) {
                window.location.href = `/prazo/${props.prazo_id}`;
            } else {
                window.location.href = `/publicacao/${props.publicacao_id}`;
            }
        }

    });

    calendar.render();

});
