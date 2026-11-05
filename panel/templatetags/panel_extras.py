import os

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def static_v(path):
    """Como {% static %}, pero agrega ?v=<mtime> para evitar usar una versión en caché."""
    url = static(path)
    try:
        ruta_absoluta = os.path.join(settings.BASE_DIR, "static", path)
        version = int(os.path.getmtime(ruta_absoluta))
    except OSError:
        version = 0
    return f"{url}?v={version}"
