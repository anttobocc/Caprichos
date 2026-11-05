"""Mensaje de WhatsApp con el detalle de un pedido confirmado."""
from urllib.parse import quote

from panel.models import ConfiguracionNegocio


def construir_mensaje(pedido):
    lineas = [
        "Hola! Quiero confirmar el siguiente pedido en Capricho:",
        "",
        f"Pedido #{pedido.pk}",
        f"Nombre: {(pedido.nombre + ' ' + pedido.apellido).strip()}",
        f"Fecha del pedido: {pedido.fecha_pedido.strftime('%d/%m/%Y')}",
        f"Entrega: {pedido.get_tipo_entrega_display()}",
    ]
    if pedido.direccion_envio:
        lineas.append(f"Dirección: {pedido.direccion_envio}")
    lineas.append("")
    lineas.append("Productos:")
    for item in pedido.items.all():
        nombre = item.nombre_producto
        if item.nombre_variante:
            nombre += f" ({item.nombre_variante})"
        lineas.append(f"- {item.cantidad} x {nombre} — ${item.precio_unitario} c/u")
    lineas.append("")
    lineas.append(f"Total: ${pedido.total}")
    if pedido.observaciones:
        lineas.append("")
        lineas.append(f"Observaciones: {pedido.observaciones}")
    return "\n".join(lineas)


def construir_url(pedido):
    config = ConfiguracionNegocio.get_solo()
    numero = config.whatsapp_numero.lstrip("+")
    return f"https://wa.me/{numero}?text={quote(construir_mensaje(pedido))}"
