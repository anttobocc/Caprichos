"""Carrito de compras basado en sesión de Django.

La sesión guarda únicamente identificadores y cantidades:

    {"<producto_id>:<variante_id o vacío>": cantidad}
    {"combo:<combo_id>": cantidad}
    {"combo:<combo_id>:<huella>": cantidad}   (combo con opciones a elección)

Las opciones elegidas de un combo viven aparte, en otra clave de sesión
({clave: [[nombre_eleccion, opcion], ...]}), y la clave del carrito lleva
una huella de esas opciones: el mismo combo con opciones distintas ocupa
líneas distintas, y la clave sigue siendo segura para usar en la URL.

El precio NUNCA se guarda en la sesión: Carrito.items() y Carrito.total()
siempre vuelven a consultar Producto/VarianteProducto/Combo en la base para
resolver el precio vigente. Esto es intencional (ver Etapa 4 y Etapa 5):
producto sin variantes -> Producto.precio; producto con variantes activas
-> VarianteProducto.precio; combo -> Combo.precio_promocional; nunca una
tercera fuente.

Las claves de producto son siempre "<id-numérico>:<...>", así que el prefijo
"combo:" (nunca numérico) no puede colisionar con ninguna clave de producto
ya guardada en una sesión existente — es 100% aditivo.

"activo" y "disponible" son conceptos distintos: un producto/variante
inactivo no puede permanecer en el carrito (se quita solo); un producto
"no disponible" sí permanece visible, pero bloquea el checkout. Combo no
tiene esa segunda distinción: si no está activo, la línea se descarta
directamente en Carrito.items(), así que una LineaCarritoCombo resuelta
siempre está disponible.
"""
import hashlib
import json

from catalogo.models import Combo, Producto, VarianteProducto

SESSION_KEY = "carrito"
SESSION_KEY_ELECCIONES = "carrito_elecciones"
PREFIJO_COMBO = "combo:"


def _clave(producto_id, variante_id):
    return f"{producto_id}:{variante_id or ''}"


def _clave_combo(combo_id, elecciones=()):
    if not elecciones:
        return f"{PREFIJO_COMBO}{combo_id}"
    huella = hashlib.sha1(json.dumps(elecciones, ensure_ascii=False).encode()).hexdigest()[:10]
    return f"{PREFIJO_COMBO}{combo_id}:{huella}"


def _elecciones_vigentes(combo, elecciones):
    """True si `elecciones` sigue cubriendo exactamente las opciones a
    elección actuales del combo (mismas elecciones, en el mismo orden, y
    cada opción todavía existe). Si el panel las cambió después de que el
    cliente agregó el combo, la línea ya no es válida."""
    vigentes = list(combo.elecciones.all())
    if len(vigentes) != len(elecciones):
        return False
    return all(
        nombre == eleccion.nombre and opcion in eleccion.lista_opciones
        for (nombre, opcion), eleccion in zip(elecciones, vigentes)
    )


class LineaCarrito:
    def __init__(self, clave, producto, variante, cantidad):
        self.clave = clave
        self.producto = producto
        self.variante = variante
        self.cantidad = cantidad

    @property
    def nombre(self):
        return self.producto.nombre

    @property
    def imagen(self):
        return self.producto.imagen

    @property
    def detalle(self):
        return self.variante.nombre if self.variante else ""

    @property
    def precio_unitario(self):
        return self.variante.precio if self.variante else self.producto.precio

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad

    @property
    def disponible(self):
        return self.producto.disponible


class LineaCarritoCombo:
    """Línea de carrito para un Combo — misma interfaz que LineaCarrito
    (clave/cantidad/nombre/imagen/precio_unitario/subtotal/disponible) para
    que las plantillas del carrito no necesiten ramificar por tipo.
    `variante` siempre es None: los combos no tienen variantes; en su lugar
    `elecciones` guarda las opciones elegidas ([[nombre, opcion], ...])."""

    def __init__(self, clave, combo, cantidad, elecciones=()):
        self.clave = clave
        self.combo = combo
        self.producto = None
        self.variante = None
        self.cantidad = cantidad
        self.elecciones = list(elecciones)

    @property
    def detalle(self):
        return " · ".join(f"{nombre}: {opcion}" for nombre, opcion in self.elecciones)

    @property
    def nombre(self):
        return self.combo.nombre

    @property
    def imagen(self):
        return self.combo.imagen

    @property
    def precio_unitario(self):
        return self.combo.precio_promocional

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad

    @property
    def disponible(self):
        return True


class Carrito:
    def __init__(self, request):
        self.session = request.session

    def _datos(self):
        return self.session.setdefault(SESSION_KEY, {})

    def _elecciones(self):
        return self.session.setdefault(SESSION_KEY_ELECCIONES, {})

    def _guardar(self):
        self.session.modified = True

    def agregar(self, producto, variante=None, cantidad=1):
        """Agrega `cantidad` unidades de `producto`/`variante` al carrito.
        No valida activo/disponible: eso es responsabilidad de la vista,
        que ya tuvo que resolver `producto`/`variante` desde la base antes
        de llamar acá."""
        datos = self._datos()
        clave = _clave(producto.pk, variante.pk if variante else None)
        datos[clave] = datos.get(clave, 0) + cantidad
        self._guardar()

    def agregar_combo(self, combo, cantidad=1, elecciones=()):
        """Agrega `cantidad` unidades de `combo` al carrito, con las opciones
        elegidas ([[nombre_eleccion, opcion], ...]). Misma no-validación que
        `agregar()`: la vista ya resolvió `combo` (activo) y validó las
        opciones antes de llamar."""
        elecciones = [list(par) for par in elecciones]
        datos = self._datos()
        clave = _clave_combo(combo.pk, elecciones)
        datos[clave] = datos.get(clave, 0) + cantidad
        if elecciones:
            self._elecciones()[clave] = elecciones
        self._guardar()

    def actualizar_cantidad(self, clave, cantidad):
        datos = self._datos()
        if clave not in datos:
            return
        if cantidad < 1:
            del datos[clave]
            self._elecciones().pop(clave, None)
        else:
            datos[clave] = cantidad
        self._guardar()

    def eliminar(self, clave):
        datos = self._datos()
        if clave in datos:
            del datos[clave]
            self._elecciones().pop(clave, None)
            self._guardar()

    def vaciar(self):
        self.session[SESSION_KEY] = {}
        self.session[SESSION_KEY_ELECCIONES] = {}
        self._guardar()

    def esta_vacio(self):
        return len(self._datos()) == 0

    def items(self, mensajes=None):
        """Devuelve la lista de LineaCarrito vigentes, resolviendo cada
        producto/variante contra la base de datos. Si un producto o su
        variante ya no existen o quedaron inactivos, se eliminan
        silenciosamente de la sesión (opcionalmente se agrega un aviso a
        `mensajes`, una lista donde la vista puede acumular textos para
        mostrar con el framework de mensajes)."""
        datos = self._datos()
        lineas = []
        claves_a_quitar = []

        for clave, cantidad in list(datos.items()):
            if clave.startswith(PREFIJO_COMBO):
                try:
                    combo_id = int(clave[len(PREFIJO_COMBO):].partition(":")[0])
                except ValueError:
                    claves_a_quitar.append(clave)
                    continue
                combo = Combo.objects.filter(pk=combo_id, activo=True).first()
                if combo is None:
                    claves_a_quitar.append(clave)
                    if mensajes is not None:
                        mensajes.append("Un combo de tu carrito ya no está disponible y fue quitado.")
                    continue
                elecciones = self._elecciones().get(clave, [])
                if not _elecciones_vigentes(combo, elecciones):
                    claves_a_quitar.append(clave)
                    if mensajes is not None:
                        mensajes.append(
                            f'Las opciones de "{combo.nombre}" cambiaron y fue quitado de tu carrito. Volvé a agregarlo.'
                        )
                    continue
                lineas.append(LineaCarritoCombo(clave, combo, cantidad, elecciones))
                continue

            producto_id_str, _, variante_id_str = clave.partition(":")
            try:
                producto_id = int(producto_id_str)
            except ValueError:
                claves_a_quitar.append(clave)
                continue

            producto = Producto.objects.filter(pk=producto_id, activo=True).first()
            if producto is None:
                claves_a_quitar.append(clave)
                if mensajes is not None:
                    mensajes.append("Un producto de tu carrito ya no está disponible y fue quitado.")
                continue

            variante = None
            if variante_id_str:
                variante = VarianteProducto.objects.filter(
                    pk=variante_id_str, producto=producto, activo=True
                ).first()
                if variante is None:
                    claves_a_quitar.append(clave)
                    if mensajes is not None:
                        mensajes.append(
                            f'Una opción de "{producto.nombre}" ya no está disponible y fue quitada de tu carrito.'
                        )
                    continue

            lineas.append(LineaCarrito(clave, producto, variante, cantidad))

        if claves_a_quitar:
            for clave in claves_a_quitar:
                datos.pop(clave, None)
                self._elecciones().pop(clave, None)
            self._guardar()

        return lineas

    def cantidad_total(self):
        return sum(linea.cantidad for linea in self.items())

    def total(self):
        return sum((linea.subtotal for linea in self.items()), start=0)

    def hay_no_disponibles(self):
        return any(not linea.disponible for linea in self.items())
