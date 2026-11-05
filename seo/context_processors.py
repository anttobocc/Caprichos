from django.conf import settings

# Apps cuyas páginas no deben aparecer en Google (panel, carrito/pedidos,
# cuentas de usuario). Se marcan con <meta name="robots" content="noindex">.
APPS_NO_INDEXABLES = {"panel", "pedidos", "usuarios"}


def seo(request):
    """URL canónica, URL base e indexabilidad para las etiquetas SEO."""
    match = getattr(request, "resolver_match", None)
    app = match.app_name if match else ""
    base = request.build_absolute_uri("/").rstrip("/")
    return {
        "seo_base_url": base,
        "seo_canonical_url": f"{base}{request.path}",
        "seo_noindex": app in APPS_NO_INDEXABLES,
        "n8n_chat_webhook_url": getattr(settings, "N8N_CHAT_WEBHOOK_URL", ""),
    }
