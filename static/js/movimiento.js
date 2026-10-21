/* Aparición al hacer scroll (ver static/css/movimiento.css).
 *
 * movimiento.css oculta estos bloques desde el primer pintado (misma
 * lista que SELECTORES); acá, con IntersectionObserver, se les agrega
 * "revelado" la primera vez que entran
 * en pantalla (una sola vez: volver a subir no los vuelve a animar).
 * Las tarjetas hermanas reciben --mov-i (0, 1, 2...) para escalonarse,
 * con tope para que la última de una grilla larga no tarde de más. */
(function () {
    "use strict";

    // Cancela el respaldo del <head> (que muestra todo si este script no
    // llega a correr).
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
