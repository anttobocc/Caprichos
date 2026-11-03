"""Información pública del negocio para el asistente de n8n.

El workflow de n8n (asistente/n8n/capricho_asistente.json) consulta esta
URL en cada mensaje antes de llamar a la IA, así el asistente responde
siempre con los productos, precios y reglas que están cargados en el
panel, sin tener que copiar nada a mano en n8n.

Solo expone datos que ya son públicos en el catálogo.
"""
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET

from catalogo.models import Combo, Producto
from panel.models import ConfiguracionNegocio


def _precio(valor):
    return None if valor is None else float(valor)


def _producto(producto, request):
    datos = {
        "nombre": producto.nombre,
        "categoria": producto.categoria.nombre,
        "descripcion": producto.descripcion_corta or producto.descripcion,
        "disponible": producto.disponible,
        "unidad_venta": producto.get_unidad_venta_display(),
        "url": request.build_absolute_uri(reverse("catalogo:producto_detalle", args=[producto.slug])),
    }
    variantes = [v for v in producto.variantes.all() if v.activo]
    if variantes:
        datos["opciones"] = [
            {"opcion": v.nombre_completo, "precio": _precio(v.precio)} for v in variantes
        ]
    else:
        datos["precio"] = _precio(producto.precio)
    return datos


def _combo(combo, request):
    return {
        "nombre": combo.nombre,
        "descripcion": combo.descripcion,
        "precio": _precio(combo.precio_promocional),
        "incluye": [f"{item.cantidad} x {item.producto.nombre}" for item in combo.items.all()],
        "a_eleccion": [
            {"eleccion": e.nombre, "opciones": [p.nombre for p in e.productos.all()]}
            for e in combo.elecciones.all()
        ],
        "url": request.build_absolute_uri(reverse("catalogo:combo_detalle", args=[combo.slug])),
    }


@require_GET
@cache_page(60 * 5)
def catalogo_json(request):
    config = ConfiguracionNegocio.get_solo()
    productos = (
        Producto.objects.filter(activo=True, categoria__activo=True)
        .select_related("categoria")
        .prefetch_related("variantes")
        .order_by("categoria__orden", "nombre")
    )
    combos = Combo.objects.filter(activo=True).prefetch_related("items__producto", "elecciones__productos")
    negocio = {
        "nombre": config.nombre_negocio,
        "eslogan": config.eslogan,
        "ciudad": "Corrientes Capital, Argentina",
        "direccion_retiro": config.direccion or "Se coordina por WhatsApp",
        "whatsapp": "+" + config.whatsapp_numero.lstrip("+"),
        "whatsapp_link": f"https://wa.me/{config.whatsapp_numero.lstrip('+')}",
        "instagram": config.instagram,
        "sitio_web": request.build_absolute_uri("/"),
        "como_pedir": (
            "El cliente arma el pedido en el sitio web (carrito), elige retiro o envío y la fecha, "
            "y al confirmar se envía el detalle por WhatsApp al negocio. No hay pago online."
        ),
        "dias_minimos_anticipacion": config.dias_anticipacion_pedido,
        "dias_maximos_anticipacion": getattr(settings, "MAX_ORDER_ADVANCE_DAYS", 10),
        "envio_a_domicilio": config.envio_habilitado,
        "zona_envio": "Corrientes Capital" if config.envio_habilitado else None,
        # El costo de envío todavía no se calcula en el sistema: se coordina por WhatsApp.
        "costo_envio": "Se coordina por WhatsApp según la zona" if config.envio_habilitado else None,
        "moneda": "ARS (pesos argentinos)",
    }
    respuesta = JsonResponse({
        "negocio": negocio,
        "productos": [_producto(p, request) for p in productos],
        "combos": [_combo(c, request) for c in combos],
    }, json_dumps_params={"ensure_ascii": False})
    respuesta["X-Robots-Tag"] = "noindex"
    return respuesta
