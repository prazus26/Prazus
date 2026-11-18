document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('form-cores');
    if (!form) return;

    const campos = form.elements;
    const erro = document.getElementById('erro-cores');
    const tranquilo = document.getElementById('limite-tranquilo');

    function atualizar() {
        const urgente = campos.limite_urgente.valueAsNumber;
        const atencao = campos.limite_atencao.valueAsNumber;

        campos.limite_atencao.setCustomValidity('');

        const numerosValidos =
            Number.isInteger(urgente) &&
            Number.isInteger(atencao) &&
            campos.limite_urgente.validity.valid &&
            campos.limite_atencao.validity.valid;

        let mensagem = '';

        if (!numerosValidos) {
            mensagem = 'Preencha os limites com números inteiros dentro dos intervalos permitidos.';
        } else if (atencao <= urgente) {
            mensagem = 'Atenção deve ser maior que urgente.';
            campos.limite_atencao.setCustomValidity(mensagem);
        }

        erro.textContent = mensagem;

        if (!mensagem) {
            tranquilo.textContent = `Mais de ${atencao} dias`;

            form.querySelectorAll('[data-dias]').forEach(function (card) {
                const dias = Number(card.dataset.dias);
                const campo = dias <= 0
                    ? 'cor_vencido'
                    : dias <= urgente
                        ? 'cor_urgente'
                        : dias <= atencao
                            ? 'cor_atencao'
                            : 'cor_tranquilo';

                card.style.backgroundColor = campos[campo].value;
            });
        }

        form.querySelectorAll('[data-campo][data-cor]').forEach(function (botao) {
            const selecionada =
                campos[botao.dataset.campo].value.toLowerCase() ===
                botao.dataset.cor.toLowerCase();

            botao.setAttribute('aria-pressed', String(selecionada));
        });
    }

    form.addEventListener('input', atualizar);
    form.addEventListener('change', atualizar);

    form.querySelectorAll('[data-campo][data-cor]').forEach(function (botao) {
        botao.addEventListener('click', function () {
            campos[botao.dataset.campo].value = botao.dataset.cor;
            atualizar();
        });
    });

    document.getElementById('restaurar-cores').addEventListener('click', function () {
        const padroes = {
            limite_urgente: 3,
            limite_atencao: 7,
            cor_vencido: '#FF8C69',
            cor_urgente: '#FCBF69',
            cor_atencao: '#F3E27A',
            cor_tranquilo: '#ADF3A0'
        };

        Object.entries(padroes).forEach(function ([nome, valor]) {
            campos[nome].value = valor;
        });

        atualizar();
    });

    form.addEventListener('submit', function (evento) {
        atualizar();

        if (!form.checkValidity()) {
            evento.preventDefault();
            form.reportValidity();
        }
    });

    atualizar();
});