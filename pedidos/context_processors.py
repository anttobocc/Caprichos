from .carrito import SESSION_KEY, Carrito
from .envio import costo_envio
from .forms import CheckoutForm
from .models import Pedido


def carrito_cantidad(request):
    """Cantidad total de unidades en el carrito."""
    datos = request.session.get(SESSION_KEY, {})
    return {"carrito_cantidad": sum(datos.values())}


def carrito_resumen(request):
    """Carrito resuelto y formulario de checkout para el panel lateral."""
    carrito = Carrito(request)
    lineas = carrito.items()

    initial = {}
    if request.user.is_authenticated:
        perfil = getattr(request.user, "perfil", None)
        initial = {
            "nombre_completo": f"{request.user.first_name} {request.user.last_name}".strip(),
            "telefono": perfil.telefono if perfil else "",
        }
    checkout_form = CheckoutForm(initial=initial)
    total = carrito.total()

    return {
        "carrito_lineas": lineas,
        "carrito_total": total,
        "carrito_hay_no_disponibles": carrito.hay_no_disponibles(),
        "carrito_checkout_form": checkout_form,
        # Costo estimado; el total final se recalcula al confirmar.
        "carrito_costo_envio": costo_envio(checkout_form.config, Pedido.TipoEntrega.ENVIO, total),
    }
