/* Variantes de producto: tres responsabilidades independientes.
 *
 * 1) Prellena las variantes de un producto NUEVO según su categoría: copia
 *    las del último producto de esa categoría (o una plantilla base si la
 *    categoría todavía no tiene productos). Solo actúa sobre paneles
 *    data-modo="crear": al editar nunca se reemplazan variantes guardadas.
 *    Depende de window.CAPRICHO_PLANTILLAS_VARIANTES, embebido por la vista:
 *    {categorias: {id: {filas: [{nombre, modalidad, modalidad_label}],
 *    usa_modalidad}}, modalidades: [[valor, etiqueta], ...]}.
 *
 * 2) Muestra la columna Modalidad (Cocinadas/Congeladas) solo en las
 *    categorías que la usan, y permite sumar filas con "+ Agregar variante"
 *    o con atajos ("Pequeña, Mediana, Grande").
 *
 * 3) Reordena las variantes arrastrando su fila (como una playlist): cada
 *    fila tiene un handle "⠿⠿" (data-arrastrar); al soltarla se recalcula
 *    el campo oculto "orden" de cada fila según su posición final en el
 *    DOM. No hay input numérico de orden visible para el usuario. */
(function () {
    "use strict";

    var datos = window.CAPRICHO_PLANTILLAS_VARIANTES || {};
    var categorias = datos.categorias || {};
    var modalidades = datos.modalidades || [];

    function crearCampo(tag, attrs) {
        var el = document.createElement(tag);
        Object.keys(attrs || {}).forEach(function (clave) {
            if (attrs[clave] !== undefined && attrs[clave] !== null) {
                el.setAttribute(clave, attrs[clave]);
            }
        });
        return el;
    }

    function campoConEtiqueta(etiqueta, hijo, modificador) {
        var contenedor = document.createElement("div");
        contenedor.className = "admin-variante-fila__campo admin-variante-fila__campo--" + modificador;
        var label = document.createElement("label");
        label.textContent = etiqueta;
        contenedor.appendChild(label);
        contenedor.appendChild(hijo);
        return contenedor;
    }

    function selectorModalidad(indice, valor) {
        var select = crearCampo("select", { name: "variantes-" + indice + "-modalidad" });
        [["", "Sin modalidad"]].concat(modalidades).forEach(function (opcion) {
            var el = crearCampo("option", { value: opcion[0] });
            el.textContent = opcion[1];
            if (opcion[0] === (valor || "")) {
                el.selected = true;
            }
            select.appendChild(el);
        });
        return select;
    }

    function construirFila(indice, fila) {
        var div = document.createElement("div");
        div.className = "admin-variante-fila";
        div.setAttribute("data-variante-fila", "");

        div.appendChild(crearCampo("input", {
            type: "hidden", name: "variantes-" + indice + "-orden", value: String(indice),
        }));

        var handle = crearCampo("button", { type: "button", "data-arrastrar": "", "aria-label": "Arrastrar para reordenar" });
        handle.className = "admin-variante-fila__handle";
        handle.textContent = "⠿⠿";
        div.appendChild(handle);

        var nombre = crearCampo("input", {
            type: "text", name: "variantes-" + indice + "-nombre", value: fila.nombre || "", placeholder: "Ej: Pequeña",
        });
        div.appendChild(campoConEtiqueta("Variante", nombre, "nombre"));
        div.appendChild(campoConEtiqueta("Modalidad", selectorModalidad(indice, fila.modalidad), "modalidad"));

        var precio = crearCampo("input", {
            type: "number", step: "0.01", min: "0", name: "variantes-" + indice + "-precio",
        });
        div.appendChild(campoConEtiqueta("Precio", precio, "precio"));

        var eliminarVacio = document.createElement("span");
        eliminarVacio.className = "admin-variante-fila__eliminar admin-variante-fila__eliminar--vacio";
        eliminarVacio.setAttribute("aria-hidden", "true");
        div.appendChild(eliminarVacio);

        return div;
    }

    function partes(panel) {
        return {
            seccion: panel.querySelector("[data-variantes-seccion]"),
            cuerpo: panel.querySelector("[data-variantes-body]"),
            total: panel.querySelector('input[name="variantes-TOTAL_FORMS"]'),
            categoria: panel.querySelector('select[name="categoria"]'),
        };
    }

    function filasDe(contenedor) {
        return Array.prototype.slice.call(contenedor.children).filter(function (el) {
            return el.hasAttribute("data-variante-fila");
        });
    }

    function indiceDe(fila) {
        var campo = fila.querySelector('input[name$="-nombre"]');
        return campo ? parseInt(campo.name.split("-")[1], 10) : NaN;
    }

    function filaNuevaVacia(fila) {
        var id = fila.querySelector('input[name$="-id"]');
        var nombre = fila.querySelector('input[name$="-nombre"]');
        var precio = fila.querySelector('input[name$="-precio"]');
        return !(id && id.value) && !(nombre && nombre.value.trim()) && !(precio && precio.value.trim());
    }

    function categoriaUsaModalidad(categoriaId) {
        var info = categorias[categoriaId];
        return !!(info && info.usa_modalidad);
    }

    function hayModalidadCargada(cuerpo) {
        return Array.prototype.some.call(
            cuerpo.querySelectorAll('select[name$="-modalidad"]'),
            function (select) { return select.value !== ""; }
        );
    }

    function aplicarModalidad(panel, limpiarSiSeOculta) {
        var p = partes(panel);
        if (!p.seccion || !p.cuerpo) {
            return;
        }
        // Al abrir un producto ya guardado, si alguna variante tiene
        // modalidad se muestra la columna aunque la categoría no la use,
        // para no esconder un dato existente.
        var visible = (p.categoria && categoriaUsaModalidad(p.categoria.value)) ||
            (!limpiarSiSeOculta && hayModalidadCargada(p.cuerpo));
        p.seccion.classList.toggle("admin-variantes--sin-modalidad", !visible);
        if (!visible && limpiarSiSeOculta) {
            p.cuerpo.querySelectorAll('select[name$="-modalidad"]').forEach(function (select) {
                select.value = "";
            });
        }
    }

    function quitarFilasVaciasDelFinal(p) {
        // Solo desde el final: quitar una fila del medio dejaría huecos en
        // los índices del formset (variantes-0, variantes-2...).
        var filas = filasDe(p.cuerpo);
        for (var i = filas.length - 1; i >= 0; i--) {
            var indice = indiceDe(filas[i]);
            if (!filaNuevaVacia(filas[i]) || indice !== parseInt(p.total.value, 10) - 1) {
                break;
            }
            filas[i].remove();
            p.total.value = String(indice);
        }
    }

    function agregarFilas(panel, filas) {
        var p = partes(panel);
        if (!p.cuerpo || !p.total) {
            return;
        }
        quitarFilasVaciasDelFinal(p);
        var existentes = filasDe(p.cuerpo).map(function (fila) {
            var nombre = fila.querySelector('input[name$="-nombre"]');
            return nombre ? nombre.value.trim().toLowerCase() : "";
        });
        var primera = null;
        filas.forEach(function (fila) {
            if (fila.nombre && existentes.indexOf(fila.nombre.toLowerCase()) !== -1) {
                return;
            }
            var indice = parseInt(p.total.value, 10) || 0;
            var nueva = construirFila(indice, fila);
            p.cuerpo.appendChild(nueva);
            p.total.value = String(indice + 1);
            primera = primera || nueva;
        });
        actualizarOrden(p.cuerpo);
        aplicarModalidad(panel, false);
        if (primera) {
            var foco = primera.querySelector(primera.querySelector('input[name$="-nombre"]').value ? 'input[name$="-precio"]' : 'input[name$="-nombre"]');
            if (foco) {
                foco.focus();
            }
        }
    }

    function repoblar(panel, categoriaId) {
        var p = partes(panel);
        if (!p.cuerpo || !p.total) {
            return;
        }
        var filas = (categorias[categoriaId] || {}).filas || [];
        p.cuerpo.innerHTML = "";
        filas.forEach(function (fila, indice) {
            p.cuerpo.appendChild(construirFila(indice, fila));
        });
        p.total.value = String(filas.length);
        aplicarModalidad(panel, true);
    }

    document.addEventListener("change", function (evento) {
        var select = evento.target.closest('select[name="categoria"]');
        var panel = select && select.closest("[data-modo]");
        if (!panel || !partes(panel).cuerpo) {
            return;
        }
        if (panel.getAttribute("data-modo") === "crear") {
            repoblar(panel, select.value);
        } else {
            aplicarModalidad(panel, true);
        }
    });

    document.addEventListener("click", function (evento) {
        var boton = evento.target.closest("[data-variante-agregar], [data-variante-atajo]");
        var panel = boton && boton.closest("[data-modo]");
        if (!panel) {
            return;
        }
        if (boton.hasAttribute("data-variante-agregar")) {
            agregarFilas(panel, [{ nombre: "", modalidad: "" }]);
        } else {
            agregarFilas(panel, boton.getAttribute("data-variante-atajo").split("|").map(function (nombre) {
                return { nombre: nombre, modalidad: "" };
            }));
        }
    });

    document.querySelectorAll("[data-modo]").forEach(function (panel) {
        aplicarModalidad(panel, false);
    });

    /* ------------------------- Arrastrar para reordenar ------------------------- */

    function actualizarOrden(contenedor) {
        var indice = 0;
        filasDe(contenedor).forEach(function (fila) {
            // La fila "extra" en blanco del formset no se toca: si le
            // reescribimos "orden", Django la considera modificada y exige
            // sus campos obligatorios aunque no se haya cargado nada.
            if (filaNuevaVacia(fila)) {
                return;
            }
            var ordenInput = fila.querySelector('input[name$="-orden"]');
            if (ordenInput) {
                ordenInput.value = String(indice);
            }
            indice += 1;
        });
    }

    var filaActiva = null;
    var contenedorActivo = null;

    document.addEventListener("pointerdown", function (evento) {
        var handle = evento.target.closest("[data-arrastrar]");
        if (!handle) {
            return;
        }
        var fila = handle.closest("[data-variante-fila]");
        if (!fila || !fila.parentElement) {
            return;
        }
        filaActiva = fila;
        contenedorActivo = fila.parentElement;
        fila.classList.add("admin-variante-fila--arrastrando");
        try {
            handle.setPointerCapture(evento.pointerId);
        } catch (err) { /* no-op: algunos navegadores viejos no soportan pointer capture */ }
        evento.preventDefault();
    });

    document.addEventListener("pointermove", function (evento) {
        if (!filaActiva || !contenedorActivo) {
            return;
        }
        var y = evento.clientY;
        var hermanas = filasDe(contenedorActivo).filter(function (f) { return f !== filaActiva; });
        for (var i = 0; i < hermanas.length; i++) {
            var hermana = hermanas[i];
            var rect = hermana.getBoundingClientRect();
            var medio = rect.top + rect.height / 2;
            var posicion = filaActiva.compareDocumentPosition(hermana);
            var hermanaEstaDespues = !!(posicion & Node.DOCUMENT_POSITION_FOLLOWING);
            if (hermanaEstaDespues && y > medio) {
                contenedorActivo.insertBefore(filaActiva, hermana.nextSibling);
                break;
            }
            if (!hermanaEstaDespues && y < medio) {
                contenedorActivo.insertBefore(filaActiva, hermana);
                break;
            }
        }
    });

    function soltar() {
        if (!filaActiva || !contenedorActivo) {
            return;
        }
        filaActiva.classList.remove("admin-variante-fila--arrastrando");
        actualizarOrden(contenedorActivo);
        filaActiva = null;
        contenedorActivo = null;
    }

    document.addEventListener("pointerup", soltar);
    document.addEventListener("pointercancel", soltar);
})();
