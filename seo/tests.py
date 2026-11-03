import json
import re

from django.test import TestCase, override_settings

from catalogo.models import Categoria, Combo, Producto


@override_settings(ALLOWED_HOSTS=["testserver"])
class SeoTests(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre="Tartas test", slug="tartas-test", activo=True)
        self.producto = Producto.objects.create(
            categoria=self.categoria, nombre="Tarta de frutillas", slug="tarta-test-frutillas",
            descripcion_corta="Tarta artesanal con crema y frutillas frescas.",
            unidad_venta="unidad", precio=17500, activo=True, disponible=True,
        )
        Producto.objects.create(
            categoria=self.categoria, nombre="Oculto", slug="oculto",
            unidad_venta="unidad", precio=1, activo=False,
        )

    def test_robots_txt(self):
        r = self.client.get("/robots.txt")
        self.assertEqual(r.status_code, 200)
        texto = r.content.decode()
        self.assertIn("Disallow: /panel/", texto)
        self.assertIn("Disallow: /checkout/", texto)
        self.assertIn("Sitemap: http://testserver/sitemap.xml", texto)

    def test_sitemap_lista_solo_contenido_publico(self):
        r = self.client.get("/sitemap.xml")
        self.assertEqual(r.status_code, 200)
        texto = r.content.decode()
        self.assertIn("/producto/tarta-test-frutillas/", texto)
        self.assertIn("/categoria/tartas-test/", texto)
        self.assertNotIn("/producto/oculto/", texto)
        self.assertNotIn("/panel/", texto)

    def test_home_tiene_un_solo_h1_meta_y_negocio_local(self):
        html = self.client.get("/").content.decode()
        self.assertEqual(len(re.findall(r"<h1[\s>]", html)), 1)
        self.assertIn('<meta name="description"', html)
        self.assertIn('<link rel="canonical" href="http://testserver/">', html)
        self.assertIn('"@type": "Bakery"', html)

    def test_producto_tiene_descripcion_y_datos_estructurados(self):
        html = self.client.get("/producto/tarta-test-frutillas/").content.decode()
        self.assertIn("Tarta de frutillas (Tarta artesanal con crema y frutillas frescas) de Capricho, pastelería artesanal en Corrientes. Desde $17.500.", html)
        self.assertIn('<meta property="og:type" content="product">', html)
        bloque = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1)
        datos = json.loads(bloque)
        self.assertEqual(datos["@type"], "Product")
        self.assertEqual(datos["offers"]["price"], "17500.00")
        self.assertEqual(datos["offers"]["priceCurrency"], "ARS")

    def test_combo_meta_y_jsonld_escapan_html(self):
        Combo.objects.create(nombre="Combo <b>merienda</b>", slug="combo-test", descripcion="Budín + tarta",
                             precio_promocional=30000, activo=True)
        html = self.client.get("/combo/combo-test/").content.decode()
        self.assertIn("Precio promocional $30.000.", html)
        self.assertNotIn("<b>merienda</b>", html)
        self.assertIn("\\u003cb\\u003e", html)

    def test_paginas_privadas_son_noindex(self):
        for url in ["/carrito/", "/login/", "/panel/login/"]:
            html = self.client.get(url).content.decode()
            self.assertIn('content="noindex, nofollow"', html, url)
            self.assertNotIn('rel="canonical"', html, url)
