from django.db import migrations

from catalogo.templatetags.catalogo_extras import quitar_prefijo_categoria


def opciones_a_productos(apps, schema_editor):
    """Convierte las opciones escritas a mano ("Frutilla, Coco") en los
    productos activos equivalentes. Primero busca coincidencia exacta con el
    nombre mostrado (sin el prefijo de la categoría, ej. "Tarta de coco" ->
    "Coco"); si no hay, una coincidencia parcial única. Las opciones que no
    coinciden con ningún producto se descartan."""
    ComboEleccion = apps.get_model("catalogo", "ComboEleccion")
    Producto = apps.get_model("catalogo", "Producto")
    productos = list(Producto.objects.filter(activo=True).select_related("categoria"))

    for eleccion in ComboEleccion.objects.all():
        elegidos = []
        for texto in (opcion.strip().lower() for opcion in eleccion.opciones.split(",")):
            if not texto:
                continue
            exactos = [
                p for p in productos
                if texto in (p.nombre.lower(), quitar_prefijo_categoria(p.nombre, p.categoria.nombre).lower())
            ]
            parciales = [p for p in productos if texto in p.nombre.lower()]
            if exactos:
                elegidos.append(exactos[0])
            elif len(parciales) == 1:
                elegidos.append(parciales[0])
        eleccion.productos.set(elegidos)


class Migration(migrations.Migration):

    dependencies = [
        ("catalogo", "0015_comboeleccion_productos"),
    ]

    operations = [
        migrations.RunPython(opciones_a_productos, migrations.RunPython.noop),
    ]
