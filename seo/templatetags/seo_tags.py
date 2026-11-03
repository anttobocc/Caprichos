"""Datos estructurados (JSON-LD de schema.org) para SEO local y de producto.

- jsonld_negocio: ficha de negocio local (Bakery) con nombre, dirección,
  teléfono (NAP), zona de envíos y redes. Es lo que Google usa junto con
  el Google Business Profile para las búsquedas locales.
- jsonld_producto / jsonld_combo: producto con precio en ARS y
  disponibilidad, para que Google pueda mostrar resultados enriquecidos.
"""
import json

from django import template
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import Truncator

register = template.Library()


def _script(datos):
    # Se escapan <, > y & para que ningún texto cargado desde el panel pueda
    # cerrar el <script> (mismo criterio que el filtro json_script de Django).
    texto = json.dumps(datos, ensure_ascii=False)
    texto = texto.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return mark_safe(f'<script type="application/ld+json">{texto}</script>')


def _absoluta(request, url):
    return request.build_absolute_uri(url) if url else None


def descripcion_meta(*textos, largo=155):
    """Primer texto no vacío, sin HTML ni saltos de línea, recortado al
    largo que Google suele mostrar en la meta description."""
    for texto in textos:
        limpio = " ".join(strip_tags(texto or "").split())
        if limpio:
            return Truncator(limpio).chars(largo)
    return ""


@register.filter
def url_segura(archivo):
    """URL de un ImageField, o "" si no tiene archivo (evita el ValueError
    de .url sobre un campo vacío)."""
    try:
        return archivo.url if archivo else ""
    except ValueError:
        return ""


@register.simple_tag
def meta_descripcion(*textos):
    return descripcion_meta(*textos)


def _precio_desde(producto):
    if producto.precio is not None:
        return producto.precio
    variante = producto.variante_mas_barata
    return variante.precio if variante else None


def _pesos(valor):
    return "$" + f"{valor:,.0f}".replace(",", ".")


@register.simple_tag
def meta_producto(producto):
    """Meta description de un producto: su descripción (si está cargada) y
    siempre nombre, precio, ciudad y forma de pedido, que es lo que busca
    la gente ("tarta de coco Corrientes", "empanadas a domicilio")."""
    nombre = producto.nombre
    if producto.descripcion_corta:
        nombre += f" ({producto.descripcion_corta.rstrip('.')})"
    partes = [f"{nombre} de Capricho, pastelería artesanal en Corrientes."]
    extra = descripcion_meta(producto.descripcion, largo=70)
    if extra:
        partes.append(extra.rstrip(".") + ".")
    precio = _precio_desde(producto)
    if precio is not None:
        partes.append(f"Desde {_pesos(precio)}.")
    partes.append("Pedí online con retiro o envío a domicilio.")
    return descripcion_meta(" ".join(partes))


@register.simple_tag
def meta_combo(combo):
    texto = f"{combo.nombre}: combo de Capricho, pastelería artesanal en Corrientes."
    propia = descripcion_meta(combo.descripcion, largo=70)
    if propia:
        texto += " " + propia.rstrip(".") + "."
    texto += f" Precio promocional {_pesos(combo.precio_promocional)}. Pedí online con retiro o envío."
    return descripcion_meta(texto)


@register.simple_tag
def meta_categoria(categoria):
    propia = descripcion_meta(categoria.descripcion, largo=80)
    texto = f"{categoria.nombre} artesanales de Capricho en Corrientes."
    if propia:
        texto += " " + propia.rstrip(".") + "."
    texto += " Mirá precios y opciones y pedí online con retiro o envío a domicilio."
    return descripcion_meta(texto)


@register.simple_tag(takes_context=True)
def jsonld_negocio(context):
    request = context["request"]
    config = context.get("configuracion_negocio")
    if config is None:
        return ""
    base = request.build_absolute_uri("/")
    datos = {
        "@context": "https://schema.org",
        "@type": "Bakery",
        "@id": f"{base}#negocio",
        "name": config.nombre_negocio,
        "description": config.eslogan,
        "url": base,
        "image": _absoluta(request, config.portada_imagen.url if config.portada_imagen else "/media/productos/portada.png"),
        "logo": _absoluta(request, "/static/img/logo.png"),
        "telephone": "+" + config.whatsapp_numero.lstrip("+"),
        "priceRange": "$$",
        "servesCuisine": ["Empanadas", "Pastelería", "Panadería"],
        "areaServed": {"@type": "City", "name": "Corrientes"},
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Corrientes",
            "addressRegion": "Corrientes",
            "addressCountry": "AR",
        },
    }
    if config.direccion:
        datos["address"]["streetAddress"] = config.direccion
    if config.instagram:
        datos["sameAs"] = [config.instagram]
    return _script(datos)


def _oferta(request, url, precio, disponible):
    return {
        "@type": "Offer",
        "url": _absoluta(request, url),
        "priceCurrency": "ARS",
        "price": f"{precio:.2f}",
        "availability": "https://schema.org/InStock" if disponible else "https://schema.org/OutOfStock",
    }


@register.simple_tag(takes_context=True)
def jsonld_producto(context, producto):
    request = context["request"]
    datos = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": producto.nombre,
        "description": descripcion_meta(producto.descripcion, producto.descripcion_corta, producto.nombre, largo=500),
        "category": producto.categoria.nombre,
        "brand": {"@type": "Brand", "name": "Capricho"},
    }
    if producto.imagen:
        datos["image"] = _absoluta(request, producto.imagen.url)
    precio = _precio_desde(producto)
    if precio is not None:
        datos["offers"] = _oferta(request, request.path, precio, producto.disponible)
    return _script(datos)


@register.simple_tag(takes_context=True)
def jsonld_combo(context, combo):
    request = context["request"]
    datos = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": combo.nombre,
        "description": descripcion_meta(combo.descripcion, combo.nombre, largo=500),
        "brand": {"@type": "Brand", "name": "Capricho"},
        "offers": _oferta(request, request.path, combo.precio_promocional, True),
    }
    if combo.imagen:
        datos["image"] = _absoluta(request, combo.imagen.url)
    return _script(datos)
