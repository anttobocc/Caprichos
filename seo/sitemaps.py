"""Sitemap del sitio público: inicio, productos, categorías y combos activos."""
from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from catalogo.models import Categoria, Combo, Producto


class BaseSitemap(Sitemap):
    # En producción (PythonAnywhere) el sitio se sirve solo por HTTPS.
    protocol = "http" if settings.DEBUG else "https"


class PaginasEstaticasSitemap(BaseSitemap):
    changefreq = "weekly"

    def items(self):
        return ["catalogo:home", "catalogo:productos"]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == "catalogo:home" else 0.8


class CategoriaSitemap(BaseSitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Categoria.objects.filter(activo=True, mostrar_en_productos=True)

    def location(self, obj):
        return reverse("catalogo:categoria_detalle", args=[obj.slug])


class ProductoSitemap(BaseSitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Producto.objects.filter(activo=True).order_by("pk")

    def location(self, obj):
        return reverse("catalogo:producto_detalle", args=[obj.slug])

    def lastmod(self, obj):
        return obj.fecha_actualizacion


class ComboSitemap(BaseSitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Combo.objects.filter(activo=True).order_by("pk")

    def location(self, obj):
        return reverse("catalogo:combo_detalle", args=[obj.slug])


SITEMAPS = {
    "paginas": PaginasEstaticasSitemap,
    "categorias": CategoriaSitemap,
    "productos": ProductoSitemap,
    "combos": ComboSitemap,
}
