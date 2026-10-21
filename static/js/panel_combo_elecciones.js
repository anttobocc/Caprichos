/* Opciones a elección del combo (panel): el selector "Categoría" de cada
 * fila filtra qué sabores (productos activos) se muestran como casillas.
 * Al cambiar de categoría se desmarcan los sabores de la anterior y se
 * marcan todos los de la nueva, para que el administrador solo tenga que
 * destildar los que no entran en el combo. La categoría no se guarda: al
 * reabrir el formulario se deduce de los sabores ya marcados. */
(function () {
    "use strict";

    function iniciar(fila) {
        var selector = fila.querySelector("[data-eleccion-categoria]");
        var opciones = fila.querySelectorAll("[data-categoria]");
        var vacio = fila.querySelector("[data-eleccion-vacio]");
        if (!selector) {
            return;
        }

        function filtrar() {
            var categoria = selector.value;
            opciones.forEach(function (opcion) {
                opcion.hidden = opcion.getAttribute("data-categoria") !== categoria;
            });
            if (vacio) {
                vacio.hidden = categoria !== "";
            }
        }

        if (!selector.value) {
            var marcada = fila.querySelector("[data-categoria] input:checked");
            if (marcada) {
                selector.value = marcada.closest("[data-categoria]").getAttribute("data-categoria");
            }
        }

        selector.addEventListener("change", function () {
            opciones.forEach(function (opcion) {
                var casilla = opcion.querySelector("input");
                if (casilla) {
                    casilla.checked = opcion.getAttribute("data-categoria") === selector.value;
                }
            });
            filtrar();
        });

        filtrar();
    }

    document.querySelectorAll("[data-eleccion]").forEach(iniciar);
})();
