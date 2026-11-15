document.addEventListener('DOMContentLoaded', function () {

    const calendarEl = document.getElementById('calendar');

    if (!calendarEl) return;

    const calendar = new FullCalendar.Calendar(calendarEl, {

        initialView: 'dayGridMonth',
        locale: 'pt-br',
        height: 'auto',
        dayMaxEvents: 3,

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
            const props = info.event.extendedProps;
            const card = document.createElement('div');
            card.className = 'prazo-card';

            const classe = document.createElement('small');
            classe.textContent = props.tipo === 'triagem'
                ? 'PUBLICAÇÃO • REVISAR'
                : props.tipo === 'prazo_personalizado'
                    ? 'PRAZO PERSONALIZADO'
                    : 'PRAZO EXTRAÍDO • CONFERIR';
            card.appendChild(classe);

            const titulo = document.createElement('strong');
            titulo.textContent = info.event.title;
            card.appendChild(titulo);

            if (props.cliente) {
                const processo = document.createElement('span');
                processo.textContent = props.numero_processo;
                card.appendChild(processo);
            }

            // Datas de triagem não são vencimentos judiciais.
            if (props.tipo !== 'triagem') {
                const dias = document.createElement('span');
                dias.className = 'prazo-card-dias';
                if (props.dias_restantes < 0) {
                    dias.textContent = `Data calculada há ${Math.abs(props.dias_restantes)} dias`;
                } else if (props.dias_restantes === 0) {
                    dias.textContent = 'Data calculada: hoje';
                } else {
                    dias.textContent = `Data calculada em ${props.dias_restantes} dias`;
                }
                card.appendChild(dias);
            }
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
