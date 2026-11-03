from django.test import TestCase, override_settings

from catalogo.models import Categoria, Producto, VarianteProducto


@override_settings(ALLOWED_HOSTS=["testserver"])
class AsistenteTests(TestCase):
    def setUp(self):
        categoria = Categoria.objects.create(nombre="Empanadas test", slug="empanadas-test", activo=True)
        self.producto = Producto.objects.create(
            categoria=categoria, nombre="Empanadas test de carne", slug="empanadas-carne-test",
            unidad_venta="docena", activo=True, disponible=True,
        )
        VarianteProducto.objects.create(producto=self.producto, nombre="Docena", precio=12000, activo=True)
        Producto.objects.create(
            categoria=categoria, nombre="Borrador", slug="borrador",
            unidad_venta="unidad", precio=1, activo=False,
        )

    def test_catalogo_json(self):
        r = self.client.get("/asistente/catalogo.json")
        self.assertEqual(r.status_code, 200)
        datos = r.json()
        self.assertIn("negocio", datos)
        productos = {p["nombre"]: p for p in datos["productos"]}
        self.assertNotIn("Borrador", productos)
        empanadas = productos["Empanadas test de carne"]
        self.assertEqual(empanadas["opciones"], [{"opcion": "Docena", "precio": 12000.0}])
        self.assertEqual(empanadas["url"], "http://testserver/producto/empanadas-carne-test/")

    @override_settings(N8N_CHAT_WEBHOOK_URL="")
    def test_chat_oculto_sin_webhook(self):
        html = self.client.get("/").content.decode()
        self.assertNotIn("data-asistente", html)

    @override_settings(N8N_CHAT_WEBHOOK_URL="https://ejemplo.app.n8n.cloud/webhook/capricho-asistente")
    def test_chat_visible_con_webhook(self):
        html = self.client.get("/").content.decode()
        self.assertIn('data-webhook="https://ejemplo.app.n8n.cloud/webhook/capricho-asistente"', html)
        self.assertIn("asistente_chat.js", html)
