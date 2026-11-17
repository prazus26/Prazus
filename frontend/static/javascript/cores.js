document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('form-cores');
    if (!form) return;
    const campos = form.elements;
    function atualizar() {
        const urgente = Number(campos.limite_urgente.value);
        const atencao = Number(campos.limite_atencao.value);
        campos.limite_atencao.setCustomValidity(atencao > urgente ? '' : 'Atenção deve ser maior que urgente.');
        document.getElementById('erro-cores').textContent = atencao > urgente ? '' : 'Atenção deve ser maior que urgente.';
        form.querySelectorAll('[data-dias]').forEach(card => {
            const dias = Number(card.dataset.dias);
            const campo = dias <= 0 ? 'cor_vencido' : dias <= urgente ? 'cor_urgente' : dias <= atencao ? 'cor_atencao' : 'cor_tranquilo';
            card.style.backgroundColor = campos[campo].value;
        });
        form.querySelectorAll('[data-campo]').forEach(botao => {
            botao.setAttribute('aria-pressed', campos[botao.dataset.campo].value.toLowerCase() === botao.dataset.cor.toLowerCase());
        });
    }
    form.addEventListener('input', atualizar);
    form.querySelectorAll('[data-campo]').forEach(botao => botao.addEventListener('click', () => {
        campos[botao.dataset.campo].value = botao.dataset.cor;
        atualizar();
    }));
    document.getElementById('restaurar-cores').addEventListener('click', () => {
        const padroes = {limite_urgente: 3, limite_atencao: 7, cor_vencido: '#FF8C69', cor_urgente: '#FCBF69', cor_atencao: '#F3E27A', cor_tranquilo: '#ADF3A0'};
        Object.entries(padroes).forEach(([nome, valor]) => { campos[nome].value = valor; });
        atualizar();
    });
    atualizar();
});
