from django.http import HttpResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

# Secciones privadas o sin valor para buscadores: panel, carrito, checkout,
# pedidos y cuentas de usuario.
RUTAS_BLOQUEADAS = [
    "/panel/",
    "/carrito/",
    "/checkout/",
    "/mis-pedidos/",
    "/pedidos/",
    "/perfil/",
    "/login/",
    "/logout/",
    "/registro/",
    "/asistente/",
]


@require_GET
@cache_control(max_age=60 * 60 * 24, public=True)
def robots_txt(request):
    lineas = ["User-agent: *", "Allow: /"]
    lineas += [f"Disallow: {ruta}" for ruta in RUTAS_BLOQUEADAS]
    lineas += ["", f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}", ""]
    return HttpResponse("\n".join(lineas), content_type="text/plain; charset=utf-8")
