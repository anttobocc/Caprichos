from .models import Combo


def navbar_combos(request):
    """Indica si hay combos activos, para mostrar el link en la navbar."""
    return {"hay_combos_activos": Combo.objects.filter(activo=True).exists()}
