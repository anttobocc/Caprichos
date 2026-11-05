/* Reordena las categorías arrastrando las filas. */
(function () {
    "use strict";

    function obtenerCookie(nombre) {
        var valor = null;
        document.cookie.split(";").forEach(function (parte) {
            var trozo = parte.trim();
            if (trozo.indexOf(nombre + "=") === 0) {
                valor = decodeURIComponent(trozo.slice(nombre.length + 1));
            }
        });
        return valor;
    }

    function filasDe(contenedor) {
        return Array.prototype.slice.call(contenedor.children).filter(function (el) {
            return el.hasAttribute("data-categoria-fila");
        });
    }

    function guardarOrden(contenedor) {
        var ids = filasDe(contenedor).map(function (fila) {
            return parseInt(fila.getAttribute("data-id"), 10);
        });
        fetch(window.CAPRICHO_CATEGORIA_REORDENAR_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": obtenerCookie("csrftoken"),
            },
            credentials: "same-origin",
            body: JSON.stringify({ orden: ids }),
        }).catch(function () {
            /* Error de red: se vuelve a guardar en el próximo cambio. */
        });
    }

    var arrastre = null;

    function iniciarArrastre(fila, evento) {
        arrastre = {
            fila: fila,
            contenedor: fila.parentElement,
            pointerId: evento.pointerId,
        };
        fila.classList.add("admin-fila--arrastrando");
    }

    document.addEventListener("pointerdown", function (evento) {
        var handle = evento.target.closest("[data-arrastrar]");
        if (!handle) {
            return;
        }
        var fila = handle.closest("[data-categoria-fila]");
        if (!fila || !fila.parentElement) {
            return;
        }
        evento.preventDefault();
        iniciarArrastre(fila, evento);
    });

    document.addEventListener("pointermove", function (evento) {
        if (!arrastre || evento.pointerId !== arrastre.pointerId) {
            return;
        }
        var y = evento.clientY;
        var hermanas = filasDe(arrastre.contenedor).filter(function (f) { return f !== arrastre.fila; });
        for (var i = 0; i < hermanas.length; i++) {
            var hermana = hermanas[i];
            var rect = hermana.getBoundingClientRect();
            var medio = rect.top + rect.height / 2;
            var posicion = arrastre.fila.compareDocumentPosition(hermana);
            var hermanaEstaDespues = !!(posicion & Node.DOCUMENT_POSITION_FOLLOWING);
            if (hermanaEstaDespues && y > medio) {
                arrastre.contenedor.insertBefore(arrastre.fila, hermana.nextSibling);
                break;
            }
            if (!hermanaEstaDespues && y < medio) {
                arrastre.contenedor.insertBefore(arrastre.fila, hermana);
                break;
            }
        }
    });

    function terminarArrastre(evento) {
        if (!arrastre || (evento && evento.pointerId !== arrastre.pointerId)) {
            return;
        }
        arrastre.fila.classList.remove("admin-fila--arrastrando");
        guardarOrden(arrastre.contenedor);
        arrastre = null;
    }

    document.addEventListener("pointerup", terminarArrastre);
    document.addEventListener("pointercancel", terminarArrastre);
})();
