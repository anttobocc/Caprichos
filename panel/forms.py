from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from django.utils.text import slugify

from catalogo.models import Categoria, Combo, ComboEleccion, Producto, VarianteProducto
from catalogo.templatetags.catalogo_extras import quitar_prefijo_categoria
from pedidos.models import Pedido

from .models import ConfiguracionNegocio


class ImagenSimpleWidget(forms.ClearableFileInput):
    """Input de imagen que solo muestra el botón de selección de archivo."""

    template_name = "panel/includes/_widget_imagen_simple.html"


def _slug_unico(model, nombre, slug_ingresado, instance_pk=None):
    """Genera un slug a partir de `nombre` si no se ingresó uno, agregando un
    sufijo numérico ante colisión (excluyendo el propio registro al editar)."""
    slug_base = slug_ingresado or slugify(nombre)
    slug = slug_base
    queryset = model.objects.all()
    if instance_pk:
        queryset = queryset.exclude(pk=instance_pk)
    contador = 2
    while queryset.filter(slug=slug).exists():
        slug = f"{slug_base}-{contador}"
        contador += 1
    return slug


class CategoriaForm(forms.ModelForm):
    """El orden y el estado activo se gestionan fuera de este formulario."""

    class Meta:
        model = Categoria
        fields = [
            "nombre", "slug", "descripcion",
            "imagen_categoria", "imagen_pos_x", "imagen_pos_y", "imagen_tamano",
            "mostrar_en_productos", "mostrar_en_inicio",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 2}),
            "slug": forms.HiddenInput(),
            "imagen_categoria": ImagenSimpleWidget(),
            "imagen_pos_x": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "imagen_pos_y": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "imagen_tamano": forms.NumberInput(attrs={"step": 1, "min": 50, "max": 5000}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        # Los completa el editor visual de imagen; si faltan, se usa el default del modelo.
        self.fields["imagen_pos_x"].required = False
        self.fields["imagen_pos_y"].required = False
        self.fields["imagen_tamano"].required = False

    def clean(self):
        cleaned = super().clean()
        nombre = cleaned.get("nombre")
        if nombre:
            cleaned["slug"] = _slug_unico(Categoria, nombre, cleaned.get("slug"), self.instance.pk)
        if cleaned.get("imagen_pos_x") in (None, ""):
            cleaned["imagen_pos_x"] = 50
        if cleaned.get("imagen_pos_y") in (None, ""):
            cleaned["imagen_pos_y"] = 50
        if cleaned.get("imagen_tamano") in (None, ""):
            cleaned["imagen_tamano"] = 260
        return cleaned


class PedidosImagenForm(forms.ModelForm):
    """Imagen de la tarjeta "Pedidos" de la portada."""

    class Meta:
        model = ConfiguracionNegocio
        fields = [
            "pedidos_imagen", "pedidos_imagen_pos_x", "pedidos_imagen_pos_y", "pedidos_imagen_tamano",
        ]
        widgets = {
            "pedidos_imagen": ImagenSimpleWidget(),
            "pedidos_imagen_pos_x": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "pedidos_imagen_pos_y": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "pedidos_imagen_tamano": forms.NumberInput(attrs={"step": 1, "min": 50, "max": 5000}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pedidos_imagen_pos_x"].required = False
        self.fields["pedidos_imagen_pos_y"].required = False
        self.fields["pedidos_imagen_tamano"].required = False

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("pedidos_imagen_pos_x") in (None, ""):
            cleaned["pedidos_imagen_pos_x"] = 50
        if cleaned.get("pedidos_imagen_pos_y") in (None, ""):
            cleaned["pedidos_imagen_pos_y"] = 50
        if cleaned.get("pedidos_imagen_tamano") in (None, ""):
            cleaned["pedidos_imagen_tamano"] = 260
        return cleaned


class PortadaImagenForm(forms.ModelForm):
    """Imagen principal del hero con su posición y zoom."""

    class Meta:
        model = ConfiguracionNegocio
        fields = [
            "portada_imagen", "portada_imagen_pos_x", "portada_imagen_pos_y", "portada_imagen_zoom",
        ]
        widgets = {
            "portada_imagen": ImagenSimpleWidget(),
            "portada_imagen_pos_x": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "portada_imagen_pos_y": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "portada_imagen_zoom": forms.NumberInput(attrs={"step": 1, "min": 100, "max": 200}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["portada_imagen_pos_x"].required = False
        self.fields["portada_imagen_pos_y"].required = False
        self.fields["portada_imagen_zoom"].required = False

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("portada_imagen_pos_x") in (None, ""):
            cleaned["portada_imagen_pos_x"] = 50
        if cleaned.get("portada_imagen_pos_y") in (None, ""):
            cleaned["portada_imagen_pos_y"] = 32
        if cleaned.get("portada_imagen_zoom") in (None, ""):
            cleaned["portada_imagen_zoom"] = 100
        return cleaned


class ProductoForm(forms.ModelForm):
    """El slug se genera al crear y no cambia al editar, para no romper URLs."""

    class Meta:
        model = Producto
        fields = [
            "categoria",
            "nombre",
            "imagen",
            "imagen_pos_x",
            "imagen_pos_y",
            "imagen_zoom",
            "precio",
            "unidad_venta",
            "destacado",
        ]
        widgets = {
            "imagen": ImagenSimpleWidget(),
            "imagen_pos_x": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "imagen_pos_y": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "imagen_zoom": forms.NumberInput(attrs={"step": 1, "min": 100, "max": 200}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["precio"].required = False
        # Los completa el editor visual de imagen.
        self.fields["imagen_pos_x"].required = False
        self.fields["imagen_pos_y"].required = False
        self.fields["imagen_zoom"].required = False

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("imagen_pos_x") in (None, ""):
            cleaned["imagen_pos_x"] = 50
        if cleaned.get("imagen_pos_y") in (None, ""):
            cleaned["imagen_pos_y"] = 50
        if cleaned.get("imagen_zoom") in (None, ""):
            cleaned["imagen_zoom"] = 100
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        # El slug se genera solo al crear, para no alterar URLs publicadas.
        if not instance.slug:
            instance.slug = _slug_unico(Producto, instance.nombre, None, instance.pk)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class VarianteProductoForm(forms.ModelForm):
    class Meta:
        model = VarianteProducto
        fields = ["nombre", "modalidad", "precio", "orden"]
        widgets = {
            "orden": forms.HiddenInput(),
            "nombre": forms.TextInput(attrs={"placeholder": "Ej: Pequeña"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Etiqueta explícita para la opción vacía.
        self.fields["modalidad"].choices = [("", "Sin modalidad"), *VarianteProducto.Modalidad.choices]


VarianteProductoFormSet = inlineformset_factory(
    Producto,
    VarianteProducto,
    form=VarianteProductoForm,
    extra=1,
    can_delete=True,
)


class ComboForm(forms.ModelForm):
    """El slug se genera al crear y no cambia al editar."""

    class Meta:
        model = Combo
        fields = [
            "nombre", "descripcion", "imagen",
            "imagen_pos_x", "imagen_pos_y", "imagen_zoom", "precio_promocional",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "imagen": ImagenSimpleWidget(),
            "imagen_pos_x": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "imagen_pos_y": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 100}),
            "imagen_zoom": forms.NumberInput(attrs={"step": 1, "min": 100, "max": 200}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["imagen_pos_x"].required = False
        self.fields["imagen_pos_y"].required = False
        self.fields["imagen_zoom"].required = False

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("imagen_pos_x") in (None, ""):
            cleaned["imagen_pos_x"] = 50
        if cleaned.get("imagen_pos_y") in (None, ""):
            cleaned["imagen_pos_y"] = 50
        if cleaned.get("imagen_zoom") in (None, ""):
            cleaned["imagen_zoom"] = 100
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = _slug_unico(Combo, instance.nombre, None, instance.pk)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ComboEleccionForm(forms.ModelForm):
    """Opciones a elegir entre los productos activos del catálogo. El filtro
    por categoría es solo de interfaz y no se guarda."""

    class Meta:
        model = ComboEleccion
        fields = ["nombre", "productos"]
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Ej: Mini tarta"}),
            "productos": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["productos"].queryset = (
            Producto.objects.filter(activo=True)
            .select_related("categoria")
            .order_by("categoria__orden", "categoria__nombre", "nombre")
        )
        self.fields["productos"].label_from_instance = lambda producto: quitar_prefijo_categoria(
            producto.nombre, producto.categoria.nombre
        )
        self.categorias = Categoria.objects.filter(productos__activo=True).distinct()
        elegidos = self.instance.productos.all() if self.instance.pk else Producto.objects.none()
        primero = elegidos.select_related("categoria").first()
        self.categoria_inicial = primero.categoria_id if primero else None

    def clean_productos(self):
        productos = self.cleaned_data["productos"]
        if len(productos) < 2:
            raise forms.ValidationError("Marcá al menos dos opciones.")
        return productos


ComboEleccionFormSet = inlineformset_factory(
    Combo,
    ComboEleccion,
    form=ComboEleccionForm,
    extra=2,
    can_delete=True,
)


class UsuarioCrearForm(UserCreationForm):
    """Alta de usuario desde el panel; permite asignar permisos de administración."""

    is_staff = forms.BooleanField(required=False, label="Permisos administrativos")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.is_staff = self.cleaned_data["is_staff"]
        usuario.is_active = True
        if commit:
            usuario.save()
        return usuario


class UsuarioEditarForm(forms.ModelForm):
    """Edición de usuario. La contraseña se cambia en una vista aparte."""

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_staff"]


class ConfiguracionNegocioForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionNegocio
        fields = [
            "nombre_negocio",
            "eslogan",
            "whatsapp_numero",
            "direccion",
            "instagram",
            "dias_anticipacion_pedido",
            "envio_habilitado",
            "costo_envio",
            "envio_gratis_desde",
        ]


class PedidoEstadoForm(forms.ModelForm):
    """Cambia solo el estado del pedido."""

    class Meta:
        model = Pedido
        fields = ["estado"]
