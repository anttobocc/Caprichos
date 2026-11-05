/* Chat flotante del asistente (n8n). */
(function () {
    "use strict";

    var raiz = document.querySelector("[data-asistente]");
    if (!raiz) return;

    var webhook = raiz.dataset.webhook;
    var whatsapp = raiz.dataset.whatsapp;
    var lanzador = raiz.querySelector("[data-asistente-abrir]");
    var panel = raiz.querySelector(".asistente__panel");
    var cerrar = raiz.querySelector("[data-asistente-cerrar]");
    var mensajes = raiz.querySelector("[data-asistente-mensajes]");
    var form = raiz.querySelector("[data-asistente-form]");
    var input = form.querySelector("input");
    var enviar = form.querySelector("button");
    var sugerencias = raiz.querySelector("[data-asistente-sugerencias]");
    var ocupado = false;

    function nuevoId() {
        if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
        return "s-" + Date.now().toString(36) + Math.random().toString(36).slice(2);
    }

    // La sesión dura lo que la pestaña: así la memoria no mezcla visitas.
    var sessionId;
    try {
        sessionId = sessionStorage.getItem("capricho_asistente_sid");
        if (!sessionId) {
            sessionId = nuevoId();
            sessionStorage.setItem("capricho_asistente_sid", sessionId);
        }
    } catch (e) {
        sessionId = nuevoId();
    }

    function abrir() {
        panel.hidden = false;
        lanzador.setAttribute("aria-expanded", "true");
        raiz.classList.add("asistente--abierto");
        input.focus();
    }

    function cerrarPanel() {
        panel.hidden = true;
        lanzador.setAttribute("aria-expanded", "false");
        raiz.classList.remove("asistente--abierto");
        lanzador.focus();
    }

    // Convierte el texto en nodos seguros (sin innerHTML).
    function pintarTexto(nodo, texto) {
        var lineas = String(texto).split("\n");
        lineas.forEach(function (linea, i) {
            if (i > 0) nodo.appendChild(document.createElement("br"));
            var partes = linea.split(/(https?:\/\/[^\s)]+|\*\*[^*]+\*\*)/g);
            partes.forEach(function (parte) {
                if (!parte) return;
                if (/^https?:\/\//.test(parte)) {
                    var a = document.createElement("a");
                    a.href = parte;
                    a.textContent = parte.indexOf("wa.me") !== -1 ? "WhatsApp" : parte.replace(/^https?:\/\/[^/]+/, "") || parte;
                    if (a.hostname !== location.hostname) {
                        a.target = "_blank";
                        a.rel = "noopener";
                    }
                    nodo.appendChild(a);
                } else if (/^\*\*.+\*\*$/.test(parte)) {
                    var b = document.createElement("strong");
                    b.textContent = parte.slice(2, -2);
                    nodo.appendChild(b);
                } else {
                    nodo.appendChild(document.createTextNode(parte));
                }
            });
        });
    }

    function agregar(texto, quien) {
        var p = document.createElement("p");
        p.className = "asistente__msg asistente__msg--" + quien;
        pintarTexto(p, texto);
        mensajes.appendChild(p);
        mensajes.scrollTop = mensajes.scrollHeight;
        return p;
    }

    function preguntar(pregunta) {
        pregunta = pregunta.trim();
        if (!pregunta || ocupado) return;
        ocupado = true;
        enviar.disabled = true;
        if (sugerencias) sugerencias.hidden = true;
        agregar(pregunta, "usuario");
        var escribiendo = agregar("Escribiendo…", "bot");
        escribiendo.classList.add("asistente__msg--escribiendo");

        fetch(webhook, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pregunta: pregunta, sessionId: sessionId })
        })
            .then(function (r) {
                if (!r.ok) throw new Error("HTTP " + r.status);
                return r.json();
            })
            .then(function (datos) {
                var respuesta = datos && (datos.respuesta || datos.output);
                if (!respuesta) throw new Error("Respuesta vacía");
                escribiendo.remove();
                agregar(respuesta, "bot");
            })
            .catch(function () {
                escribiendo.remove();
                agregar("Uy, no pude responder en este momento. Probá de nuevo en un ratito o escribinos por " + whatsapp, "bot");
            })
            .finally(function () {
                ocupado = false;
                enviar.disabled = false;
                input.focus();
            });
    }

    lanzador.addEventListener("click", function () {
        if (panel.hidden) abrir(); else cerrarPanel();
    });
    cerrar.addEventListener("click", cerrarPanel);
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && !panel.hidden) cerrarPanel();
    });
    form.addEventListener("submit", function (e) {
        e.preventDefault();
        var texto = input.value;
        input.value = "";
        preguntar(texto);
    });
    if (sugerencias) {
        sugerencias.addEventListener("click", function (e) {
            if (e.target.tagName === "BUTTON") preguntar(e.target.textContent);
        });
    }
})();
