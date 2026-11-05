"""Control de acceso al panel: requiere un usuario activo con is_staff."""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def es_administrador(user):
    return user.is_authenticated and user.is_active and user.is_staff


def panel_admin_required(view_func):
    """Sin login redirige al login del panel; sin permisos devuelve 403."""

    @login_required(login_url="panel:login")
    @wraps(view_func)
    def _envoltorio(request, *args, **kwargs):
        if not es_administrador(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _envoltorio
