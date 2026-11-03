from django.conf import settings

# Apps cuyas páginas no deben aparecer en Google (panel, carrito/pedidos,
# cuentas de usuario). Se marcan con <meta name="robots" content="noindex">.
APPS_NO_INDEXABLES = {"panel", "pedidos", "usuarios"}


def seo(request):
    """Datos comunes para las etiquetas SEO de base.html: URL canónica
    (sin parámetros de búsqueda), URL base absoluta para Open Graph y si la
    página es indexable."""
    match = getattr(request, "resolver_match", None)
    app = match.app_name if match else ""
    base = request.build_absolute_uri("/").rstrip("/")
    return {
        "seo_base_url": base,
        "seo_canonical_url": f"{base}{request.path}",
        "seo_noindex": app in APPS_NO_INDEXABLES,
        "n8n_chat_webhook_url": getattr(settings, "N8N_CHAT_WEBHOOK_URL", ""),
    }
