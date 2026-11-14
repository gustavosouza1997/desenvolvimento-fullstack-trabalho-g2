/*
 * Máscaras de preenchimento sem bibliotecas externas.
 * Basta colocar data-mascara="cpf" ou data-mascara="telefone" no <input>.
 */

function aplicarMascaraCpf(valor) {
    var numeros = valor.replace(/\D/g, '').slice(0, 11);

    return numeros
        .replace(/^(\d{3})(\d)/, '$1.$2')
        .replace(/^(\d{3})\.(\d{3})(\d)/, '$1.$2.$3')
        .replace(/\.(\d{3})(\d{1,2})$/, '.$1-$2');
}

function aplicarMascaraTelefone(valor) {
    var numeros = valor.replace(/\D/g, '').slice(0, 11);

    if (numeros.length <= 2) {
        return numeros.replace(/^(\d{1,2})/, '($1');
    }
    if (numeros.length <= 6) {
        return numeros.replace(/^(\d{2})(\d+)/, '($1) $2');
    }
    if (numeros.length <= 10) {
        // Fixo: (51) 3333-4444
        return numeros.replace(/^(\d{2})(\d{4})(\d+)/, '($1) $2-$3');
    }
    // Celular: (51) 99999-8888
    return numeros.replace(/^(\d{2})(\d{5})(\d+)/, '($1) $2-$3');
}

var mascaras = {
    cpf: aplicarMascaraCpf,
    telefone: aplicarMascaraTelefone
};

document.addEventListener('DOMContentLoaded', function () {
    var campos = document.querySelectorAll('[data-mascara]');

    campos.forEach(function (campo) {
        var mascara = mascaras[campo.dataset.mascara];
        if (!mascara) {
            return;
        }

        // Formata o valor que já veio do banco (ex.: na edição)
        campo.value = mascara(campo.value);

        campo.addEventListener('input', function () {
            campo.value = mascara(campo.value);
        });
    });
});
