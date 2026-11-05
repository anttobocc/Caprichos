from urllib.parse import quote

from .models import ConfiguracionNegocio


def _google_maps_url(direccion):
    """Link de Google Maps para la dirección del negocio (agrega la ciudad si falta)."""
    if not direccion:
        return ""
    consulta = direccion if "corrientes" in direccion.lower() else f"{direccion}, Corrientes, Argentina"
    return f"https://www.google.com/maps/search/?api=1&query={quote(consulta)}"


def configuracion_negocio(request):
    """Configuración del negocio disponible en todos los templates."""
    config = ConfiguracionNegocio.get_solo()
    return {
        "configuracion_negocio": config,
        "whatsapp_link_general": f"https://wa.me/{config.whatsapp_numero.lstrip('+')}",
        "google_maps_url": _google_maps_url(config.direccion),
    }
