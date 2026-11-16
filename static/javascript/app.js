document.addEventListener('DOMContentLoaded', function () {
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) return;

    function adicionarLinha(card, tag, valor, classe) {
        if (valor == null || String(valor).trim() === '') return;
        const elemento = document.createElement(tag);
        if (classe) elemento.className = classe;
        elemento.textContent = String(valor);
        card.appendChild(elemento);
    }

    function descricaoCurta(evento) {
        const props = evento.extendedProps;
        if (props.tipo === 'pericia') {
            if (!evento.allDay && evento.start) {
                const hora = evento.start.toLocaleTimeString('pt-BR', {
                    hour: '2-digit', minute: '2-digit'
                });
                return `Perícia médica - ${hora}`;
            }
            return 'Perícia médica';
        }
        if (props.tipo === 'prazo_provisorio') {
            const atividade = String(props.nome_prazo || 'Atividade com data-limite');
            // Atividade completa e justificativa permanecem nos detalhes ao clicar.
            if (/quesitos/i.test(atividade)) return 'Quesitos complementares';
            return atividade.length > 56 ? atividade.slice(0, 53) + '...' : atividade;
        }
        return props.nome_prazo || 'Prazo';
    }

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
            }
        },
        eventContent: function (info) {
            const evento = info.event;
            const props = evento.extendedProps;
            const card = document.createElement('div');
            card.className = 'prazo-card'; // Preserva o estilo original do Prazus

            const numero = String(props.numero_processo || '').trim();
            const cliente = String(props.cliente || '').trim();
            // Não repetir o número como título e segunda linha.
            adicionarLinha(card, 'strong', cliente || (numero ? `Processo ${numero}` : evento.title));
            if (cliente && numero) adicionarLinha(card, 'span', `Processo ${numero}`);

            if (props.tipo === 'pericia') {
                adicionarLinha(card, 'span', descricaoCurta(evento));
                adicionarLinha(card, 'span', 'Compromisso automático', 'prazo-card-dias');
            } else if (props.tipo === 'prazo_provisorio') {
                const dias = props.quantidade_dias;
                const contagem = props.tipo_contagem === 'uteis' ? 'úteis' : 'corridos';
                if (Number.isInteger(dias)) {
                    adicionarLinha(card, 'span', `${dias} dias ${contagem} antes da perícia`);
                }
                adicionarLinha(card, 'span', descricaoCurta(evento));
                adicionarLinha(card, 'span', 'Prévia não validada', 'prazo-card-dias');
                // Justificativa jurídica completa acessível por hover e pela tela de detalhes.
                card.title = props.aviso || 'Data provisória sujeita a verificação';
            } else {
                adicionarLinha(card, 'span', descricaoCurta(evento));
                if (props.dias_restantes == null) {
                    adicionarLinha(card, 'span', 'Data a conferir', 'prazo-card-dias');
                } else if (props.dias_restantes < 0) {
                    adicionarLinha(card, 'span', `Vencido há ${Math.abs(props.dias_restantes)} dias`, 'prazo-card-dias');
                } else if (props.dias_restantes === 0) {
                    adicionarLinha(card, 'span', 'Vence hoje', 'prazo-card-dias');
                } else {
                    adicionarLinha(card, 'span', `${props.dias_restantes} dias restantes`, 'prazo-card-dias');
                }
                if (props.origem_prazo === 'estimativa_prazus') {
                    adicionarLinha(card, 'small', 'Estimativa histórica');
                }
            }
            return { domNodes: [card] };
        },
        eventClick: function (info) {
            info.jsEvent.preventDefault();
            const props = info.event.extendedProps;
            if (props.prazo_id) {
                window.location.href = `/prazo/${encodeURIComponent(props.prazo_id)}`;
            } else if (props.publicacao_id) {
                window.location.href = `/publicacao/${encodeURIComponent(props.publicacao_id)}`;
            }
        }
    });
    calendar.render();
});
