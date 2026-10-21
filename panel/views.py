import json

from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from catalogo.models import Categoria, Combo, Producto, VarianteProducto
from pedidos.models import Pedido

from .forms import (
    CategoriaForm,
    ComboForm,
    ComboEleccionFormSet,
    ConfiguracionNegocioForm,
    PedidoEstadoForm,
    PedidosImagenForm,
    PortadaImagenForm,
    ProductoForm,
    UsuarioCrearForm,
    UsuarioEditarForm,
    VarianteProductoFormSet,
)
from .models import ConfiguracionNegocio
from .permisos import panel_admin_required

FILAS_POR_PAGINA = 20

# Variantes predeterminadas por categoría (cantidad, y opcionalmente
# modalidad para productos con dos ejes de compra como Empanadas). Al crear
# un producto nuevo, el panel prellena estas filas en JS según la categoría
# elegida; el administrador solo completa el precio de cada combinación.
# Primero se copian las variantes del último producto cargado en esa
# categoría (así una categoría nueva, como Pastafrola, "aprende" sus
# tamaños del primer producto que se carga); este diccionario es solo el
# punto de partida para categorías que todavía no tienen productos.
PLANTILLAS_VARIANTES_POR_CATEGORIA = {
    "empanadas": {
        "cantidades": ["Unidad", "Media docena", "Docena"],
        "modalidades": [("cocinada", "Cocinadas"), ("congelada", "Congeladas")],
    },
    "alfajores": {
        "cantidades": ["Media docena", "Docena"],
        "modalidades": [],
    },
    "dulces": {  # Tartas (el slug interno de la categoría es "dulces")
        "cantidades": ["Pequeña", "Mediana", "Grande"],
        "modalidades": [],
    },
}


def _plantilla_variantes(categoria_slug):
    plantilla = PLANTILLAS_VARIANTES_POR_CATEGORIA.get(categoria_slug)
    if not plantilla:
        return []
    modalidades = plantilla["modalidades"] or [("", "")]
    return [
        {"nombre": cantidad, "modalidad": valor, "modalidad_label": etiqueta}
        for cantidad in plantilla["cantidades"]
        for valor, etiqueta in modalidades
    ]


def _plantilla_desde_productos(categoria):
    """Variantes activas del producto más reciente de la categoría que
    tenga variantes, en su orden, sin precios."""
    producto = (
        Producto.objects.filter(categoria=categoria, variantes__activo=True)
        .order_by("-fecha_creacion")
        .first()
    )
    if producto is None:
        return []
    return [
        {"nombre": v.nombre, "modalidad": v.modalidad, "modalidad_label": v.get_modalidad_display() if v.modalidad else ""}
        for v in producto.variantes.filter(activo=True).order_by("orden", "pk")
    ]


def _plantillas_variantes_json():
    categorias = {}
    for categoria in Categoria.objects.all():
        filas = _plantilla_desde_productos(categoria) or _plantilla_variantes(categoria.slug)
        categorias[categoria.pk] = {
            "filas": filas,
            # La columna Modalidad (Cocinadas/Congeladas) solo se muestra en
            # categorías que la usan; en el resto queda oculta y vacía.
            "usa_modalidad": any(fila["modalidad"] for fila in filas),
        }
    return json.dumps({
        "categorias": categorias,
        "modalidades": [[valor, etiqueta] for valor, etiqueta in VarianteProducto.Modalidad.choices],
    })


def _paginar(request, queryset):
    paginador = Paginator(queryset, FILAS_POR_PAGINA)
    return paginador.get_page(request.GET.get("page"))


class PanelLoginView(LoginView):
    template_name = "panel/login.html"
    redirect_authenticated_user = True


class PanelLogoutView(LogoutView):
    next_page = reverse_lazy("panel:login")


@panel_admin_required
def dashboard(request):
    contexto = {
        "total_productos": Producto.objects.count(),
        "total_categorias": Categoria.objects.count(),
        "total_usuarios": User.objects.count(),
        "pedidos_recientes": Pedido.objects.order_by("-fecha_creacion")[:8],
    }
    return render(request, "panel/dashboard.html", contexto)


@panel_admin_required
def usuarios_lista(request):
    query = request.GET.get("q", "").strip()
    usuarios = User.objects.all().order_by("username")
    if query:
        usuarios = usuarios.filter(username__icontains=query)
    pagina = _paginar(request, usuarios)
    for usuario in pagina:
        usuario.form_editar = UsuarioEditarForm(instance=usuario, auto_id=f"id_usuario_{usuario.pk}_%s")
    return render(request, "panel/usuarios_lista.html", {
        "usuarios": pagina,
        "q": query,
        "form_crear": UsuarioCrearForm(),
    })


@panel_admin_required
def usuario_crear(request):
    if request.method == "POST":
        form = UsuarioCrearForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect("panel:usuarios")
    else:
        form = UsuarioCrearForm()
    return render(request, "panel/usuario_form.html", {"form": form, "modo": "crear"})


@panel_admin_required
def usuario_editar(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UsuarioEditarForm(request.POST, instance=usuario)
        if form.is_valid():
            es_uno_mismo = usuario.pk == request.user.pk
            if es_uno_mismo and not form.cleaned_data["is_staff"]:
                messages.error(request, "No podés quitarte tus propios permisos administrativos.")
                return render(request, "panel/usuario_form.html", {"form": form, "modo": "editar", "usuario": usuario})
            form.save()
            messages.success(request, "Usuario actualizado correctamente.")
            return redirect("panel:usuarios")
    else:
        form = UsuarioEditarForm(instance=usuario)
    return render(request, "panel/usuario_form.html", {"form": form, "modo": "editar", "usuario": usuario})


@panel_admin_required
@require_POST
def usuario_toggle_activo(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if usuario.pk == request.user.pk:
        messages.error(request, "No podés desactivar tu propia cuenta.")
        return redirect("panel:usuarios")
    usuario.is_active = request.POST.get("activo") == "on"
    usuario.save(update_fields=["is_active"])
    estado = "activado" if usuario.is_active else "desactivado"
    messages.success(request, f'"{usuario.username}" fue {estado}.')
    return redirect("panel:usuarios")


@panel_admin_required
@require_POST
def usuario_eliminar(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if usuario.pk == request.user.pk:
        messages.error(request, "No podés eliminar tu propia cuenta.")
        return redirect("panel:usuarios")
    nombre = usuario.username
    usuario.delete()
    messages.success(request, f'El usuario "{nombre}" fue eliminado.')
    return redirect("panel:usuarios")


@panel_admin_required
def usuario_password(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = SetPasswordForm(usuario, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Contraseña de "{usuario.username}" actualizada correctamente.')
            return redirect("panel:usuarios")
    else:
        form = SetPasswordForm(usuario)
    return render(request, "panel/usuario_password.html", {"form": form, "usuario": usuario})


@panel_admin_required
def categorias_lista(request):
    query = request.GET.get("q", "").strip()
    categorias = Categoria.objects.order_by("orden", "nombre")
    if query:
        categorias = categorias.filter(nombre__icontains=query)
    pagina = _paginar(request, categorias)
    for categoria in pagina:
        categoria.form_editar = CategoriaForm(instance=categoria, auto_id=f"id_categoria_{categoria.pk}_%s")
    configuracion_negocio = ConfiguracionNegocio.get_solo()
    return render(request, "panel/categorias_lista.html", {
        "categorias": pagina,
        "q": query,
        "form_crear": CategoriaForm(),
        "configuracion_negocio": configuracion_negocio,
        "form_pedidos": PedidosImagenForm(instance=configuracion_negocio, auto_id="id_pedidos_%s"),
        "form_portada": PortadaImagenForm(instance=configuracion_negocio, auto_id="id_portada_%s"),
    })


@panel_admin_required
def categoria_crear(request):
    if request.method == "POST":
        form = CategoriaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría creada correctamente.")
            return redirect("panel:categorias")
    else:
        form = CategoriaForm()
    return render(request, "panel/categoria_form.html", {"form": form, "modo": "crear"})


@panel_admin_required
def categoria_editar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        form = CategoriaForm(request.POST, request.FILES, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría actualizada correctamente.")
            return redirect("panel:categorias")
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, "panel/categoria_form.html", {"form": form, "modo": "editar", "categoria": categoria})


@panel_admin_required
@require_POST
def pedidos_imagen_editar(request):
    config = ConfiguracionNegocio.get_solo()
    form = PedidosImagenForm(request.POST, request.FILES, instance=config)
    if form.is_valid():
        form.save()
        messages.success(request, 'Imagen de "Pedidos" actualizada correctamente.')
    return redirect("panel:categorias")


@panel_admin_required
@require_POST
def portada_imagen_editar(request):
    config = ConfiguracionNegocio.get_solo()
    form = PortadaImagenForm(request.POST, request.FILES, instance=config)
    if form.is_valid():
        form.save()
        messages.success(request, "Imagen principal de la portada actualizada correctamente.")
    return redirect("panel:categorias")


@panel_admin_required
@require_POST
def categoria_toggle_activo(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    categoria.activo = request.POST.get("activo") == "on"
    categoria.save(update_fields=["activo"])
    estado = "activada" if categoria.activo else "desactivada"
    messages.success(request, f'"{categoria.nombre}" fue {estado}.')
    return redirect("panel:categorias")


@panel_admin_required
@require_POST
def categoria_reordenar(request):
    """Guarda el nuevo orden tras arrastrar y soltar una fila en la lista
    de categorías (ver static/js/panel_categorias_orden.js). Recibe
    {"orden": [id, id, ...]} en el orden visual final; cada id se
    corresponde con una posición (índice) que pasa a ser su "orden"."""
    try:
        datos = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "Cuerpo de la petición inválido."}, status=400)

    orden_ids = datos.get("orden")
    if not isinstance(orden_ids, list) or not orden_ids:
        return JsonResponse({"ok": False, "error": "Falta la lista de orden."}, status=400)

    categorias = Categoria.objects.filter(pk__in=orden_ids)
    categorias_por_id = {categoria.pk: categoria for categoria in categorias}
    if len(categorias_por_id) != len(set(orden_ids)):
        return JsonResponse({"ok": False, "error": "Alguna categoría no existe."}, status=400)

    actualizadas = []
    for indice, categoria_id in enumerate(orden_ids):
        categoria = categorias_por_id[categoria_id]
        categoria.orden = indice
        actualizadas.append(categoria)
    Categoria.objects.bulk_update(actualizadas, ["orden"])

    return JsonResponse({"ok": True})


@panel_admin_required
@require_POST
def categoria_eliminar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    nombre = categoria.nombre
    categoria.delete()
    messages.success(request, f'La categoría "{nombre}" fue eliminada.')
    return redirect("panel:categorias")


def _variantes_activas(formset):
    """Variantes que quedarían activas tras guardar el formset (no marcadas
    para borrar). El formulario ya no expone "activo": toda variante que
    llega hasta acá se crea/mantiene activa (default del modelo), así que
    alcanza con que tenga datos y no esté marcada para eliminar."""
    activas = []
    for form in formset.forms:
        if not form.cleaned_data:
            continue
        if form.cleaned_data.get("DELETE"):
            continue
        activas.append(form)
    return activas


def _validar_coherencia_precio(prod_form, formset):
    """Producto sin variantes activas -> precio obligatorio.
    Producto con variantes activas -> precio debe quedar vacío (error
    explícito si se cargó, nunca se limpia solo)."""
    precio = prod_form.cleaned_data.get("precio")
    hay_variantes_activas = bool(_variantes_activas(formset))
    if hay_variantes_activas and precio is not None:
        prod_form.add_error(
            "precio",
            "Un producto con variantes debe tener el precio del producto vacío.",
        )
        return False
    if not hay_variantes_activas and precio is None:
        prod_form.add_error(
            "precio",
            "Un producto sin variantes debe tener un precio.",
        )
        return False
    return True


@panel_admin_required
def productos_lista(request):
    query = request.GET.get("q", "").strip()
    # Ordenado por categoría primero para que el template pueda agruparlos
    # visualmente con {% ifchanged %} sin tocar la estructura de datos ni
    # duplicar productos.
    productos = Producto.objects.select_related("categoria").order_by("categoria__orden", "categoria__nombre", "nombre")
    if query:
        productos = productos.filter(nombre__icontains=query)
    pagina = _paginar(request, productos)
    for producto in pagina:
        producto.form_editar = ProductoForm(instance=producto, auto_id=f"id_producto_{producto.pk}_%s")
        producto.formset_editar = VarianteProductoFormSet(
            instance=producto, prefix="variantes", auto_id=f"id_producto_{producto.pk}_%s",
        )
    return render(request, "panel/productos_lista.html", {
        "productos": pagina,
        "q": query,
        "form_crear": ProductoForm(),
        "formset_crear": VarianteProductoFormSet(prefix="variantes"),
        "plantillas_variantes_json": _plantillas_variantes_json(),
    })


@panel_admin_required
def producto_crear(request):
    if request.method == "POST":
        prod_form = ProductoForm(request.POST, request.FILES)
        formset = VarianteProductoFormSet(request.POST, prefix="variantes")
        if prod_form.is_valid() and formset.is_valid():
            if _validar_coherencia_precio(prod_form, formset):
                producto = prod_form.save()
                formset.instance = producto
                formset.save()
                messages.success(request, "Producto creado correctamente.")
                return redirect("panel:productos")
    else:
        prod_form = ProductoForm()
        formset = VarianteProductoFormSet(prefix="variantes")
    return render(request, "panel/producto_form.html", {
        "form": prod_form, "formset": formset, "modo": "crear",
        "plantillas_variantes_json": _plantillas_variantes_json(),
    })


@panel_admin_required
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        prod_form = ProductoForm(request.POST, request.FILES, instance=producto)
        formset = VarianteProductoFormSet(request.POST, instance=producto, prefix="variantes")
        if prod_form.is_valid() and formset.is_valid():
            if _validar_coherencia_precio(prod_form, formset):
                prod_form.save()
                formset.save()
                messages.success(request, "Producto actualizado correctamente.")
                return redirect("panel:productos")
    else:
        prod_form = ProductoForm(instance=producto)
        formset = VarianteProductoFormSet(instance=producto, prefix="variantes")
    return render(request, "panel/producto_form.html", {
        "form": prod_form, "formset": formset, "modo": "editar", "producto": producto,
        "plantillas_variantes_json": _plantillas_variantes_json(),
    })


@panel_admin_required
@require_POST
def producto_toggle_activo(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.activo = request.POST.get("activo") == "on"
    producto.save(update_fields=["activo"])
    estado = "activado" if producto.activo else "desactivado"
    messages.success(request, f'"{producto.nombre}" fue {estado}.')
    return redirect("panel:productos")


@panel_admin_required
@require_POST
def producto_toggle_disponible(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.disponible = request.POST.get("disponible") == "on"
    producto.save(update_fields=["disponible"])
    estado = "disponible" if producto.disponible else "no disponible"
    messages.success(request, f'"{producto.nombre}" quedó {estado}.')
    return redirect("panel:productos")


@panel_admin_required
@require_POST
def producto_toggle_destacado(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.destacado = request.POST.get("destacado") == "on"
    producto.save(update_fields=["destacado"])
    estado = "destacado" if producto.destacado else "quitado de destacados"
    messages.success(request, f'"{producto.nombre}" quedó {estado}.')
    return redirect("panel:productos")


@panel_admin_required
@require_POST
def producto_eliminar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    nombre = producto.nombre
    producto.delete()
    messages.success(request, f'El producto "{nombre}" fue eliminado.')
    return redirect("panel:productos")


@panel_admin_required
def pedidos_lista(request):
    query = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "").strip()
    # "asc" = fecha de pedido más antigua primero; cualquier otro valor (o
    # ausente) = más reciente primero, el orden por defecto de siempre.
    orden = request.GET.get("orden", "").strip()
    orden_campo = "fecha_pedido" if orden == "asc" else "-fecha_pedido"
    pedidos = Pedido.objects.order_by(orden_campo, "-pk")
    if query:
        pedidos = pedidos.filter(
            models.Q(nombre__icontains=query)
            | models.Q(apellido__icontains=query)
            | models.Q(telefono__icontains=query)
        )
    if estado:
        pedidos = pedidos.filter(estado=estado)
    return render(request, "panel/pedidos_lista.html", {
        "pedidos": _paginar(request, pedidos),
        "q": query,
        "estado": estado,
        "estados": Pedido.Estado.choices,
        "orden": orden,
    })


@panel_admin_required
def pedido_detalle(request, pk):
    pedido = get_object_or_404(Pedido.objects.select_related("usuario").prefetch_related("items"), pk=pk)
    items = list(pedido.items.all())
    subtotal = sum((item.subtotal for item in items), start=0)
    costo_envio = pedido.total - subtotal
    form = PedidoEstadoForm(instance=pedido)
    return render(request, "panel/pedido_detalle.html", {
        "pedido": pedido,
        "items": items,
        "subtotal": subtotal,
        "costo_envio": costo_envio,
        "form": form,
    })


@panel_admin_required
@require_POST
def pedido_cambiar_estado(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    form = PedidoEstadoForm(request.POST, instance=pedido)
    if form.is_valid():
        form.save()
        messages.success(request, f"El pedido #{pedido.pk} quedó en estado \"{pedido.get_estado_display()}\".")
    else:
        messages.error(request, "No se pudo actualizar el estado del pedido.")
    return redirect("panel:pedido_detalle", pk=pedido.pk)


@panel_admin_required
def configuracion(request):
    config = ConfiguracionNegocio.get_solo()
    if request.method == "POST":
        form = ConfiguracionNegocioForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Configuración actualizada correctamente.")
            return redirect("panel:configuracion")
    else:
        form = ConfiguracionNegocioForm(instance=config)
    return render(request, "panel/configuracion_form.html", {"form": form})


@panel_admin_required
def combos_lista(request):
    combos = Combo.objects.order_by("nombre").prefetch_related("elecciones")
    pagina = _paginar(request, combos)
    for combo in pagina:
        combo.form_editar = ComboForm(instance=combo, auto_id=f"id_combo_{combo.pk}_%s")
        combo.formset_editar = ComboEleccionFormSet(instance=combo, prefix="elecciones", auto_id=f"id_combo_{combo.pk}_%s")
    return render(request, "panel/combos_lista.html", {
        "combos": pagina,
        "form_crear": ComboForm(),
        "formset_crear": ComboEleccionFormSet(prefix="elecciones"),
    })


@panel_admin_required
def combo_crear(request):
    if request.method == "POST":
        form = ComboForm(request.POST, request.FILES)
        formset = ComboEleccionFormSet(request.POST, prefix="elecciones")
        if form.is_valid() and formset.is_valid():
            combo = form.save()
            formset.instance = combo
            formset.save()
            messages.success(request, "Combo creado correctamente.")
            return redirect("panel:combos")
    else:
        form = ComboForm()
        formset = ComboEleccionFormSet(prefix="elecciones")
    return render(request, "panel/combo_form.html", {"form": form, "formset": formset, "modo": "crear"})


@panel_admin_required
def combo_editar(request, pk):
    combo = get_object_or_404(Combo, pk=pk)
    if request.method == "POST":
        form = ComboForm(request.POST, request.FILES, instance=combo)
        formset = ComboEleccionFormSet(request.POST, instance=combo, prefix="elecciones")
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Combo actualizado correctamente.")
            return redirect("panel:combos")
    else:
        form = ComboForm(instance=combo)
        formset = ComboEleccionFormSet(instance=combo, prefix="elecciones")
    return render(request, "panel/combo_form.html", {
        "form": form, "formset": formset, "modo": "editar", "combo": combo,
    })


@panel_admin_required
@require_POST
def combo_toggle_activo(request, pk):
    combo = get_object_or_404(Combo, pk=pk)
    combo.activo = request.POST.get("activo") == "on"
    combo.save(update_fields=["activo"])
    estado = "activado" if combo.activo else "desactivado"
    messages.success(request, f'"{combo.nombre}" fue {estado}.')
    return redirect("panel:combos")


@panel_admin_required
@require_POST
def combo_eliminar(request, pk):
    combo = get_object_or_404(Combo, pk=pk)
    nombre = combo.nombre
    combo.delete()
    messages.success(request, f'El combo "{nombre}" fue eliminado.')
    return redirect("panel:combos")
