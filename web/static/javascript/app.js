document.addEventListener('DOMContentLoaded', function () {
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) return;

    const seletor = document.getElementById('cal-seletor');
    const formulario = document.getElementById('cal-form-periodo');
    const campoMes = document.getElementById('cal-mes');
    const campoAno = document.getElementById('cal-ano');
    const titulo = document.getElementById('cal-titulo');
    const botoesVisao = document.querySelectorAll('[data-cal-view]');
    const expandidos = new Set();
    const diasSemana = [
        'domingo', 'segunda', 'terça', 'quarta',
        'quinta', 'sexta', 'sábado'
    ];

    function adicionarLinha(container, tag, texto, classe) {
        if (texto == null || String(texto).trim() === '') return;

        const elemento = document.createElement(tag);
        elemento.textContent = String(texto);
        elemento.title = String(texto);

        if (classe) elemento.className = classe;
        container.appendChild(elemento);
    }

    function urlDetalhes(props) {
        if (props.manual_id) {
            return `/prazos-manuais/${encodeURIComponent(props.manual_id)}`;
        }

        if (props.publicacao_id) {
            return `/publicacao/${encodeURIComponent(props.publicacao_id)}`;
        }

        if (props.prazo_id) {
            return `/prazo/${encodeURIComponent(props.prazo_id)}`;
        }

        return null;
    }

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        eventDisplay: 'block',
        locale: 'pt-br',
        firstDay: 1,
        height: 'auto',
        fixedWeekCount: false,
        dayMaxEvents: false,
        headerToolbar: false,

        dayHeaderContent: function (info) {
            return diasSemana[info.date.getDay()];
        },

        datesSet: function (info) {
            titulo.textContent = info.view.title;
            campoMes.value = info.view.currentStart.getMonth();
            campoAno.value = info.view.currentStart.getFullYear();

            botoesVisao.forEach(function (botao) {
                botao.setAttribute(
                    'aria-pressed',
                    String(botao.dataset.calView === info.view.type)
                );
            });
        },

        eventDataTransform: function (dados) {
            return { ...dados, url: '' };
        },

        events: {
            url: '/api/calendario/eventos',
            method: 'GET',

            failure: function (erro) {
                console.error('Erro ao carregar eventos:', erro);
            }
        },

        eventContent: function (info) {
            const evento = info.event;
            const props = evento.extendedProps;
            const aberto = expandidos.has(evento.id);
            const cliente = props.cliente || 'Cliente não identificado';
            const processo = props.numero_processo || 'Processo não informado';
            const compromisso = props.nome_prazo || evento.title;
            const dias = Number.isInteger(props.dias_restantes)
                ? props.dias_restantes
                : props.quantidade_dias;
            const textoDias = Number.isInteger(dias)
                ? `${dias} dias`
                : '— dias';

            const card = document.createElement('div');
            card.className = 'prazo-card';

            const conteudo = document.createElement('div');
            conteudo.className = 'prazo-conteudo';
            card.appendChild(conteudo);

            const botao = document.createElement('button');
            botao.type = 'button';
            botao.className = 'prazo-resumo';
            botao.setAttribute('aria-expanded', String(aberto));
            botao.setAttribute(
                'aria-label',
                `${cliente}. ${processo}. ${textoDias}. ${compromisso}. Expandir ou recolher.`
            );
            botao.title = `${cliente} — ${compromisso}`;

            const linhas = document.createElement('div');
            linhas.className = 'prazo-linhas';

            adicionarLinha(linhas, 'strong', cliente);
            adicionarLinha(linhas, 'span', processo);
            adicionarLinha(linhas, 'span', textoDias);
            adicionarLinha(linhas, 'span', compromisso);

            botao.appendChild(linhas);
            conteudo.appendChild(botao);

            const detalhes = document.createElement('div');
            detalhes.className = 'prazo-detalhes';
            detalhes.hidden = !aberto;
            detalhes.inert = !aberto;

            if (props.manual_id) {
                adicionarLinha(detalhes, 'small', 'Origem manual');
            }

            if (!evento.allDay && info.timeText) {
                adicionarLinha(detalhes, 'span', info.timeText);
            }

            adicionarLinha(detalhes, 'p', props.aviso, 'prazo-aviso');

            const destino = urlDetalhes(props);

            if (destino) {
                const link = document.createElement('a');
                link.href = destino;
                link.className = 'prazo-link';
                link.textContent = 'Abrir detalhes';
                detalhes.appendChild(link);
            }

            conteudo.appendChild(detalhes);

            let animacaoAtual = null;

            botao.addEventListener('click', function () {
                const elementoEvento = botao.closest('.fc-event');
                if (!elementoEvento) return;

                const alturaInicial = card.getBoundingClientRect().height;

                if (animacaoAtual) {
                    animacaoAtual.onfinish = null;
                    animacaoAtual.cancel();
                    animacaoAtual = null;
                }

                card.style.height = `${alturaInicial}px`;

                const expandir = !expandidos.has(evento.id);

                if (expandir) {
                    expandidos.add(evento.id);
                } else {
                    expandidos.delete(evento.id);
                }

                function aplicarEstado(estado) {
                    elementoEvento.classList.toggle(
                        'prazo-expandido',
                        estado
                    );
                    detalhes.hidden = !estado;
                }

                aplicarEstado(expandir);

                const alturaFinal = conteudo.getBoundingClientRect().height;

                if (!expandir) {
                    aplicarEstado(true);
                }

                botao.setAttribute('aria-expanded', String(expandir));
                detalhes.inert = !expandir;

                function finalizar() {
                    aplicarEstado(expandir);
                    card.style.removeProperty('height');
                    animacaoAtual = null;
                }

                if (
                    typeof card.animate !== 'function' ||
                    Math.abs(alturaInicial - alturaFinal) < 1
                ) {
                    finalizar();
                    return;
                }

                const animacao = card.animate(
                    [
                        { height: `${alturaInicial}px` },
                        { height: `${alturaFinal}px` }
                    ],
                    {
                        duration: 350,
                        easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
                        fill: 'forwards'
                    }
                );

                animacaoAtual = animacao;

                animacao.onfinish = function () {
                    if (animacaoAtual !== animacao) return;

                    aplicarEstado(expandir);
                    card.style.height = `${alturaFinal}px`;
                    animacao.cancel();
                    finalizar();
                };
            });

            return { domNodes: [card] };
        },

        eventDidMount: function (info) {
            info.el.classList.toggle(
                'prazo-expandido',
                expandidos.has(info.event.id)
            );
        }
    });

    document.getElementById('cal-hoje').addEventListener('click', function () {
        calendar.today();
    });

    document.getElementById('cal-anterior').addEventListener('click', function () {
        calendar.prev();
    });

    document.getElementById('cal-proximo').addEventListener('click', function () {
        calendar.next();
    });

    formulario.addEventListener('submit', function (evento) {
        evento.preventDefault();
        if (!formulario.reportValidity()) return;

        const ano = Number(campoAno.value);
        const mes = Number(campoMes.value);

        if (!Number.isInteger(ano) || ano < 1000 || ano > 9999) return;

        calendar.gotoDate(new Date(ano, mes, 1));
        seletor.open = false;
    });

    botoesVisao.forEach(function (botao) {
        botao.addEventListener('click', function () {
            calendar.changeView(botao.dataset.calView);
        });
    });

    document.addEventListener('click', function (evento) {
        if (!seletor.contains(evento.target)) {
            seletor.open = false;
        }
    });

    document.addEventListener('keydown', function (evento) {
        if (evento.key === 'Escape' && seletor.open) {
            seletor.open = false;
            seletor.querySelector('summary').focus();
        }
    });

    calendar.render();
});