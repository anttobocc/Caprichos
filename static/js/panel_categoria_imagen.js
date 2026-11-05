/* Editor visual de posición y tamaño de imagen. */
(function () {
    "use strict";

    function clamp(valor, minimo, maximo) {
        return Math.min(maximo, Math.max(minimo, valor));
    }

    function numero(valor, porDefecto) {
        var n = parseFloat(valor);
        return isNaN(n) ? porDefecto : n;
    }

    function iniciar(editor) {
        var form = editor.closest("form");
        if (!form) {
            return;
        }
        var modo = editor.getAttribute("data-modo") === "recorte" ? "recorte" : "flotante";
        var lienzo = editor.querySelector("[data-lienzo]");
        var img = editor.querySelector("[data-imagen-preview]");
        var vacio = editor.querySelector("[data-imagen-vacio]");
        var slider = editor.querySelector("[data-tamano-slider]");
        var campoArchivo = form.querySelector('input[type="file"]');
        var nombreArchivo = editor.parentElement ? editor.parentElement.querySelector("[data-nombre-archivo]") : null;
        if (!nombreArchivo) {
            nombreArchivo = form.querySelector("[data-nombre-archivo]");
        }
        var campoX = form.querySelector('input[name$="pos_x"]');
        var campoY = form.querySelector('input[name$="pos_y"]');
        var campoTercero = form.querySelector('input[name$="tamano"], input[name$="zoom"]');
        if (!img || !lienzo || !campoX || !campoY || !campoTercero) {
            return;
        }

        var POS_MIN = numero(campoX.min, 0);
        var POS_MAX = numero(campoX.max, 100);
        var POS_DEFAULT = modo === "flotante" ? 50 : 50;
        var TERCERO_MIN = numero(campoTercero.min, modo === "flotante" ? 50 : 100);
        var TERCERO_MAX = numero(campoTercero.max, modo === "flotante" ? 5000 : 200);
        var TERCERO_DEFAULT = numero(campoTercero.value, modo === "flotante" ? 260 : 100);
        var PASO_BOTON = modo === "flotante" ? 1 : 2;
        // Referencia fija para convertir % <-> px en el modo "flotante".
        var PIXELES_REFERENCIA_FLOTANTE = 200;
        // En modo "recorte" el eje X se invierte al arrastrar.
        var SIGNO = modo === "recorte" ? -1 : 1;

        var x = numero(campoX.value, POS_DEFAULT);
        var y = numero(campoY.value, POS_DEFAULT);
        var tercero = numero(campoTercero.value, TERCERO_DEFAULT);

        function aplicarPosicion() {
            x = clamp(x, POS_MIN, POS_MAX);
            y = clamp(y, POS_MIN, POS_MAX);
            if (modo === "recorte") {
                img.style.objectPosition = x + "% " + y + "%";
            } else {
                // Constante fija: el editor puede estar oculto y medir 0.
                var offsetX = ((x - 50) / 100) * PIXELES_REFERENCIA_FLOTANTE;
                var offsetY = ((y - 50) / 100) * PIXELES_REFERENCIA_FLOTANTE;
                img.style.transform = "translate(" + offsetX + "px, " + offsetY + "px)";
            }
            campoX.value = String(Math.round(x));
            campoY.value = String(Math.round(y));
        }

        function aplicarTercero() {
            tercero = clamp(tercero, TERCERO_MIN, TERCERO_MAX);
            if (modo === "recorte") {
                img.style.transform = "scale(" + (tercero / 100) + ")";
            } else {
                img.style.height = tercero + "px";
            }
            campoTercero.value = String(Math.round(tercero));
            if (slider) {
                slider.value = String(Math.round(tercero));
            }
        }

        img.addEventListener("pointerdown", function (evento) {
            if (img.hidden) {
                return;
            }
            evento.preventDefault();
            var inicioX = evento.clientX;
            var inicioY = evento.clientY;
            var origenX = x;
            var origenY = y;
            var ancho = modo === "recorte" ? (lienzo.clientWidth || 1) : PIXELES_REFERENCIA_FLOTANTE;
            var alto = modo === "recorte" ? (lienzo.clientHeight || 1) : PIXELES_REFERENCIA_FLOTANTE;

            function mover(e) {
                var deltaPorcentualX = ((e.clientX - inicioX) / ancho) * 100;
                var deltaPorcentualY = ((e.clientY - inicioY) / alto) * 100;
                x = origenX + SIGNO * deltaPorcentualX;
                y = origenY + SIGNO * deltaPorcentualY;
                aplicarPosicion();
            }

            function soltar() {
                document.removeEventListener("pointermove", mover);
                document.removeEventListener("pointerup", soltar);
            }

            document.addEventListener("pointermove", mover);
            document.addEventListener("pointerup", soltar);
        });

        campoX.addEventListener("input", function () {
            x = numero(campoX.value, POS_DEFAULT);
            aplicarPosicion();
        });

        campoY.addEventListener("input", function () {
            y = numero(campoY.value, POS_DEFAULT);
            aplicarPosicion();
        });

        editor.querySelectorAll("[data-ajustar-x]").forEach(function (boton) {
            boton.addEventListener("click", function () {
                x += SIGNO * (numero(boton.getAttribute("data-ajustar-x"), 0)) * PASO_BOTON;
                aplicarPosicion();
            });
        });

        editor.querySelectorAll("[data-ajustar-y]").forEach(function (boton) {
            boton.addEventListener("click", function () {
                y += SIGNO * (numero(boton.getAttribute("data-ajustar-y"), 0)) * PASO_BOTON;
                aplicarPosicion();
            });
        });

        if (slider) {
            slider.addEventListener("input", function () {
                tercero = numero(slider.value, TERCERO_DEFAULT);
                aplicarTercero();
            });
        }

        campoTercero.addEventListener("input", function () {
            tercero = numero(campoTercero.value, TERCERO_DEFAULT);
            aplicarTercero();
        });

        if (campoArchivo) {
            campoArchivo.addEventListener("change", function () {
                var archivo = campoArchivo.files && campoArchivo.files[0];
                if (!archivo || !window.FileReader) {
                    return;
                }
                var lector = new FileReader();
                lector.onload = function (evento) {
                    img.src = evento.target.result;
                    img.hidden = false;
                    if (vacio) {
                        vacio.hidden = true;
                    }
                    if (nombreArchivo) {
                        nombreArchivo.textContent = archivo.name;
                        nombreArchivo.classList.remove("admin-imagen-archivo__nombre--vacio");
                    }
                    aplicarPosicion();
                    aplicarTercero();
                };
                lector.readAsDataURL(archivo);
            });
        }

        aplicarPosicion();
        aplicarTercero();
    }

    document.querySelectorAll("[data-imagen-editor]").forEach(iniciar);
})();
