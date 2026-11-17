document.addEventListener('DOMContentLoaded', function () {
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) return;

    function adicionarLinha(card, tag, valor, classe) {
        if (valor == null || String(valor).trim() === '') return;
        const elemento = document.createElement(tag);
        if (classe) elemento.className = classe;
        elemento.textContent = String(valor);
        elemento.title = String(valor);
        card.appendChild(elemento);
    }

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        eventDisplay: 'block',
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
            }
        },
        eventContent: function (info) {
            const evento = info.event;
            const props = evento.extendedProps;
            const card = document.createElement('div');
            card.className = 'prazo-card'; // Preserva o estilo original do Prazus

            adicionarLinha(card, 'strong', props.cliente || 'Cliente não identificado');
            adicionarLinha(card, 'span', props.numero_processo || 'Processo não informado');
            const dias = Number.isInteger(props.dias_restantes) ? props.dias_restantes : props.quantidade_dias;
            adicionarLinha(card, 'span', Number.isInteger(dias) ? `${dias} dias` :
                '— dias');
            adicionarLinha(card, 'span', props.nome_prazo || evento.title, 'prazo-card-compromisso');
            card.title = props.aviso || '';
            return { domNodes: [card] };
        },
        eventClick: function (info) {
            info.jsEvent.preventDefault();
            const props = info.event.extendedProps;
            if (props.publicacao_id) {
                window.location.href = `/publicacao/${encodeURIComponent(props.publicacao_id)}`;
            } else if (props.prazo_id) {
                window.location.href = `/prazo/${encodeURIComponent(props.prazo_id)}`;
            }
        }
    });
    calendar.render();
});
