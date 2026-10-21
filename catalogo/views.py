import json

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Categoria, Combo, Producto


def home(request):
    categorias = Categoria.objects.filter(activo=True, mostrar_en_inicio=True)
    destacados = Producto.objects.filter(activo=True, destacado=True).select_related("categoria")
    combos = Combo.objects.filter(activo=True)
    return render(request, "catalogo/home.html", {
        "categorias": categorias, "destacados": destacados, "combos": combos,
    })


def lista_productos(request):
    productos = Producto.objects.filter(activo=True).select_related("categoria")
    categoria_slug = request.GET.get("categoria")
    categoria_actual = None
    if categoria_slug:
        categoria_actual = get_object_or_404(Categoria, slug=categoria_slug, activo=True, mostrar_en_productos=True)
        productos = productos.filter(categoria=categoria_actual)
    # Combo no tiene categoría propia, así que solo aparece en el listado
    # general ("Todos"): en cuanto se filtra por una categoría puntual se
    # excluye naturalmente, sin necesidad de un caso especial en el filtro.
    combos = Combo.objects.filter(activo=True) if not categoria_actual else Combo.objects.none()
    return render(request, "catalogo/productos_lista.html", {
        "productos": productos,
        "combos": combos,
        "categorias": Categoria.objects.filter(activo=True, mostrar_en_productos=True),
        "categoria_actual": categoria_actual,
    })


def combos_publico(request):
    # Los combos ya se muestran en su sección del inicio: esta URL queda
    # solo para no romper enlaces viejos y lleva directo a esa sección.
    return redirect(f"{reverse('catalogo:home')}#combos")


def combo_detalle(request, slug):
    combo = get_object_or_404(Combo.objects.prefetch_related("elecciones"), slug=slug, activo=True)
    return render(request, "catalogo/combo_detalle.html", {
        "combo": combo,
    })


def categoria_detalle(request, slug):
    categoria = get_object_or_404(Categoria, slug=slug, activo=True, mostrar_en_productos=True)
    productos = categoria.productos.filter(activo=True)
    return render(request, "catalogo/categoria_detalle.html", {
        "categoria": categoria, "productos": productos,
    })


def producto_detalle(request, slug):
    producto = get_object_or_404(Producto.objects.select_related("categoria"), slug=slug, activo=True)
    variantes = producto.variantes.filter(activo=True) if producto.tiene_variantes else None
    contexto = {"producto": producto, "variantes": variantes}

    if variantes is not None and producto.tiene_modalidad:
        # Empanadas y cualquier otro producto con dos ejes de compra
        # (cantidad x modalidad): se arman dos selectores independientes en
        # vez de una lista plana de combinaciones (ver VarianteProducto).
        cantidades, vistas_cantidades = [], set()
        modalidades, vistas_modalidades = [], set()
        mapa = {}
        for variante in variantes:
            if variante.nombre not in vistas_cantidades:
                vistas_cantidades.add(variante.nombre)
                cantidades.append(variante.nombre)
            if variante.modalidad and variante.modalidad not in vistas_modalidades:
                vistas_modalidades.add(variante.modalidad)
                modalidades.append((variante.modalidad, variante.get_modalidad_display()))
            mapa[f"{variante.nombre}|{variante.modalidad}"] = {
                "id": variante.pk, "precio": str(variante.precio),
            }
        contexto.update({
            "cantidades": cantidades,
            "modalidades": modalidades,
            "variantes_mapa_json": json.dumps(mapa),
        })

    return render(request, "catalogo/producto_detalle.html", contexto)
