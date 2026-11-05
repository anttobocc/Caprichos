from decimal import Decimal

from .models import Pedido


def costo_envio(config, tipo_entrega, subtotal):
    """Costo de envío, calculado siempre en el servidor."""
    if tipo_entrega != Pedido.TipoEntrega.ENVIO:
        return Decimal("0")
    if not config.envio_habilitado:
        return Decimal("0")
    if config.envio_gratis_desde is not None and subtotal >= config.envio_gratis_desde:
        return Decimal("0")
    return config.costo_envio or Decimal("0")
