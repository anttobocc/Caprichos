/* Aparición de elementos al hacer scroll. */
(function () {
    "use strict";

    // Cancela el respaldo definido en el <head>.
    clearTimeout(window.__movimientoRespaldo);

    // Mantener sincronizada con el :is(...) de movimiento.css.
    var SELECTORES = [
        ".seccion-titulo",
        ".categoria-card",
        ".producto-card",
        ".m-card",
        ".producto-detalle__imagen",
        ".producto-detalle__info",
        ".pagina-listado h1",
        ".categorias-nav",
    ];
    var TOPE_ESCALONADO = 5;

    var elementos = Array.prototype.slice.call(document.querySelectorAll(SELECTORES.join(",")));

    elementos.forEach(function (el) {
        var hermanos = Array.prototype.filter.call(el.parentElement.children, function (h) {
            return h.matches(SELECTORES.join(","));
        });
        var indice = hermanos.indexOf(el);
        if (indice > 0) {
            el.style.setProperty("--mov-i", String(Math.min(indice, TOPE_ESCALONADO)));
        }
    });

    function revelar(el) {
        el.classList.add("revelado");
    }

    if (!("IntersectionObserver" in window)) {
        elementos.forEach(revelar);
        return;
    }

    var observador = new IntersectionObserver(function (entradas) {
        entradas.forEach(function (entrada) {
            if (entrada.isIntersecting) {
                revelar(entrada.target);
                observador.unobserve(entrada.target);
            }
        });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });

    elementos.forEach(function (el) {
        observador.observe(el);
    });
})();
