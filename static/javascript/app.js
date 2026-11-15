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

        events: {
            url: '/api/calendario/eventos',
            method: 'GET',

            failure: function (error) {
                console.error('Erro ao carregar eventos:', error);
            },

            success: function (eventos) {
                console.log('Eventos recebidos:', eventos.length);
            }
        },

        dateClick: function (info) {
            console.log('Dia selecionado:', info.dateStr);
        },

        eventContent: function (info) {
            const evento = info.event;
            const props = evento.extendedProps;

            const card = document.createElement('div');
            card.className = 'prazo-card';

            const titulo = document.createElement('strong');
            titulo.textContent = evento.title;

            const processo = document.createElement('span');
            processo.textContent = props.numero_processo;

            const tipo = document.createElement('span');
            tipo.textContent = props.nome_prazo;

            const dias = document.createElement('span');
            dias.className = 'prazo-card-dias';

            if (props.dias_restantes < 0) {
                dias.textContent = `Vencido há ${Math.abs(props.dias_restantes)} dias`;
            } else if (props.dias_restantes === 0) {
                dias.textContent = 'Vence hoje';
            } else {
                dias.textContent = `${props.dias_restantes} dias restantes`;
            }

            if (props.origem_prazo === 'estimativa_prazus') {
                const estimativa = document.createElement('small');
                estimativa.textContent = 'Estimativa';
                card.appendChild(estimativa);
            }

            card.appendChild(titulo);
            card.appendChild(processo);
            card.appendChild(tipo);
            card.appendChild(dias);

            return { domNodes: [card] };
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
