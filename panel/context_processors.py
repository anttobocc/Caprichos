from urllib.parse import quote

from .models import ConfiguracionNegocio


def _google_maps_url(direccion):
    """Link de búsqueda de Google Maps para la dirección del negocio. Si la
    dirección no nombra la ciudad, se agrega Corrientes para que Maps no
    la busque en otra ciudad con una calle del mismo nombre."""
    if not direccion:
        return ""
    consulta = direccion if "corrientes" in direccion.lower() else f"{direccion}, Corrientes, Argentina"
    return f"https://www.google.com/maps/search/?api=1&query={quote(consulta)}"


def configuracion_negocio(request):
    """Expone la configuración del negocio (WhatsApp, dirección, envíos,
    anticipación) a todos los templates públicos, para no hardcodear estos
    datos en el header/footer."""
    config = ConfiguracionNegocio.get_solo()
    return {
        "configuracion_negocio": config,
        "whatsapp_link_general": f"https://wa.me/{config.whatsapp_numero.lstrip('+')}",
        "google_maps_url": _google_maps_url(config.direccion),
    }
