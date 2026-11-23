from django.test import SimpleTestCase
from django.urls import resolve

from productos.api.serializer import ProductosSerializer, PreciosProductosSerializer
from productos.models import Categorias, Descuentos, Marcas, Productos


class ProductosSerializerTests(SimpleTestCase):
    def test_incluye_datos_del_producto_y_nombres_de_relaciones(self):
        producto = Productos(
            id_producto=7,
            nombre="Cera",
            descripcion="Fijación mate",
            stock_actual=12,
            stock_minimo=3,
            estado=True,
            id_marca=Marcas(id_marca=2, nombre="Barber"),
            id_categoria=Categorias(id_categoria=4, nombre="Cabello"),
            id_descuento=Descuentos(
                id_descuento=5,
                nombre="Mayorista",
                mayorista=True,
                cantidad="10.00",
            ),
        )

        data = ProductosSerializer(producto).data

        self.assertEqual(data["id_producto"], 7)
        self.assertEqual(data["stock_actual"], 12)
        self.assertEqual(data["id_marca"], 2)
        self.assertEqual(data["marca_nombre"], "Barber")
        self.assertEqual(data["categoria_nombre"], "Cabello")
        self.assertEqual(data["descuento_nombre"], "Mayorista")

    def test_precios_historicos_aceptan_valores_ausentes(self):
        data = PreciosProductosSerializer({
            "id_producto": 7,
            "costo_ultima_compra": None,
            "precio_ultima_venta": "2500.00",
        }).data

        self.assertEqual(data, {
            "id_producto": 7,
            "costo_ultima_compra": None,
            "precio_ultima_venta": "2500.00",
        })


class ProductosApiRoutesTests(SimpleTestCase):
    def test_expone_crud_y_listas_de_referencias(self):
        rutas = {
            "/api/productos/": "productos-list",
            "/api/productos/7/": "productos-detail",
            "/api/productos/precios/": "productos-precios",
            "/api/marcas/": "marcas-list",
            "/api/categorias/": "categorias-list",
            "/api/descuentos/": "descuentos-list",
        }

        for ruta, nombre in rutas.items():
            with self.subTest(ruta=ruta):
                self.assertEqual(resolve(ruta).url_name, nombre)
