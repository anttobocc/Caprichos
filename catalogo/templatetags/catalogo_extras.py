"""Filtros de presentación para nombres de producto."""
from django import template

register = template.Library()

_CONECTORES = ("de la ", "de las ", "de los ", "del ", "de ")


def quitar_prefijo_categoria(nombre, categoria_nombre):
    if not nombre or not categoria_nombre:
        return nombre

    palabras = nombre.split()
    if not palabras:
        return nombre

    primera = palabras[0].lower()
    cat = categoria_nombre.strip().lower()
    candidatos = {cat, cat.rstrip("s"), cat + "s"}
    if primera not in candidatos:
        return nombre

    resto = " ".join(palabras[1:]).strip()
    if not resto:
        return nombre

    resto_lower = resto.lower()
    for conector in _CONECTORES:
        if resto_lower.startswith(conector):
            resto = resto[len(conector):]
            break

    resto = resto.strip()
    if not resto:
        return nombre

    return resto[0].upper() + resto[1:]


@register.filter
def nombre_sin_categoria(producto):
    """Nombre del producto sin el prefijo de su categoría (solo para mostrar)."""
    categoria = getattr(producto, "categoria", None)
    if categoria is None:
        return getattr(producto, "nombre", producto)
    return quitar_prefijo_categoria(producto.nombre, categoria.nombre)
