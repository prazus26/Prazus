document.addEventListener('DOMContentLoaded', function () {

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

            events: '/api/calendario/eventos',

            dateClick: function (info) {
                alert('Dia clicado: ' + info.dateStr);
            },

            eventClick: function (info) {

                const evento = info.event;
                const processo = evento.extendedProps.numero_processo;
                const status = evento.extendedProps.status;

                alert(
                    'Prazo do processo: ' + processo +
                    '\nData: ' + evento.start.toLocaleDateString('pt-BR') +
                    '\nStatus: ' + status
                );
            }

        });

        calendar.render();
    }

});
