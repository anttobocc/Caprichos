/* Selector de fecha para el campo fecha_pedido. */
(function () {
    "use strict";

    var MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
    var DIAS = ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"];

    function pad2(n) {
        return n < 10 ? "0" + n : "" + n;
    }

    function parseISO(iso) {
        var partes = iso.split("-").map(Number);
        return new Date(partes[0], partes[1] - 1, partes[2]);
    }

    function toISO(fecha) {
        return fecha.getFullYear() + "-" + pad2(fecha.getMonth() + 1) + "-" + pad2(fecha.getDate());
    }

    function formatLargo(fecha) {
        return DIAS[fecha.getDay()] + " " + fecha.getDate() + " " + MESES[fecha.getMonth()];
    }

    function todosLosPickers() {
        return document.querySelectorAll("[data-fecha-picker]");
    }

    function construirGrilla(picker) {
        var grid = picker.querySelector("[data-fecha-picker-grid]");
        var input = picker.querySelector("[data-fecha-picker-input]");
        if (!grid || !input || grid.dataset.armado === "1") {
            return;
        }
        if (!picker.dataset.min || !picker.dataset.max) {
            return;
        }
        var min = parseISO(picker.dataset.min);
        var max = parseISO(picker.dataset.max);
        var seleccionActual = input.value;

        var frag = document.createDocumentFragment();
        var cursor = new Date(min.getTime());
        var tope = 0;
        while (cursor <= max && tope < 60) {
            var iso = toISO(cursor);
            var boton = document.createElement("button");
            boton.type = "button";
            boton.setAttribute("role", "option");
            boton.className = "fecha-picker__dia";
            boton.dataset.valor = iso;
            if (iso === seleccionActual) {
                boton.classList.add("fecha-picker__dia--activo");
                boton.setAttribute("aria-selected", "true");
            } else {
                boton.setAttribute("aria-selected", "false");
            }
            boton.innerHTML =
                '<span class="fecha-picker__dia-nombre">' + DIAS[cursor.getDay()] + "</span>" +
                '<span class="fecha-picker__dia-numero">' + cursor.getDate() + "</span>" +
                '<span class="fecha-picker__dia-mes">' + MESES[cursor.getMonth()] + "</span>";
            frag.appendChild(boton);
            cursor.setDate(cursor.getDate() + 1);
            tope += 1;
        }
        grid.appendChild(frag);
        grid.dataset.armado = "1";
    }

    function actualizarResumen(picker) {
        var input = picker.querySelector("[data-fecha-picker-input]");
        var texto = picker.querySelector("[data-fecha-picker-texto]");
        if (!input || !texto) {
            return;
        }
        if (input.value) {
            texto.textContent = formatLargo(parseISO(input.value));
            texto.classList.remove("fecha-picker__texto--vacio");
        } else {
            texto.textContent = "Elegí una fecha";
            texto.classList.add("fecha-picker__texto--vacio");
        }
    }

    function cerrar(picker) {
        var panel = picker.querySelector("[data-fecha-picker-panel]");
        var boton = picker.querySelector("[data-fecha-picker-resumen]");
        if (panel) {
            panel.hidden = true;
        }
        picker.classList.remove("fecha-picker--abierto");
        if (boton) {
            boton.setAttribute("aria-expanded", "false");
        }
    }

    function cerrarTodosMenos(picker) {
        todosLosPickers().forEach(function (p) {
            if (p !== picker) {
                cerrar(p);
            }
        });
    }

    function abrir(picker) {
        construirGrilla(picker);
        cerrarTodosMenos(picker);
        var panel = picker.querySelector("[data-fecha-picker-panel]");
        var boton = picker.querySelector("[data-fecha-picker-resumen]");
        if (panel) {
            panel.hidden = false;
        }
        picker.classList.add("fecha-picker--abierto");
        if (boton) {
            boton.setAttribute("aria-expanded", "true");
        }
    }

    document.addEventListener("click", function (evento) {
        var botonResumen = evento.target.closest("[data-fecha-picker-resumen]");
        if (botonResumen) {
            var picker = botonResumen.closest("[data-fecha-picker]");
            if (picker.classList.contains("fecha-picker--abierto")) {
                cerrar(picker);
            } else {
                abrir(picker);
            }
            return;
        }

        var dia = evento.target.closest(".fecha-picker__dia");
        if (dia) {
            var picker2 = dia.closest("[data-fecha-picker]");
            var input = picker2.querySelector("[data-fecha-picker-input]");
            input.value = dia.dataset.valor;
            input.dispatchEvent(new Event("change", { bubbles: true }));

            picker2.querySelectorAll(".fecha-picker__dia").forEach(function (b) {
                b.classList.remove("fecha-picker__dia--activo");
                b.setAttribute("aria-selected", "false");
            });
            dia.classList.add("fecha-picker__dia--activo");
            dia.setAttribute("aria-selected", "true");

            actualizarResumen(picker2);
            cerrar(picker2);
            return;
        }

        if (!evento.target.closest("[data-fecha-picker]")) {
            cerrarTodosMenos(null);
        }
    });

    document.addEventListener("keydown", function (evento) {
        if (evento.key === "Escape") {
            cerrarTodosMenos(null);
        }
    });

    document.addEventListener("DOMContentLoaded", function () {
        todosLosPickers().forEach(function (picker) {
            construirGrilla(picker);
            actualizarResumen(picker);
        });
    });
})();
