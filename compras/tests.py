from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from django.urls import resolve

from compras.api.serializer import CompraCreateSerializer, CompraSerializer


class ComprasApiTests(SimpleTestCase):
    def test_publica_ruta_de_listado_y_creacion(self):
        self.assertEqual(resolve('/api/compras/').url_name, 'compras-list')

    def test_rechaza_cantidades_invalidas(self):
        serializer = CompraCreateSerializer(data={
            'detalles': [
                {'id_producto': 7, 'cantidad': 0, 'precio_unitario': '15.50'},
            ],
        })

        self.assertFalse(serializer.is_valid())

    def test_rechaza_productos_repetidos(self):
        serializer = CompraCreateSerializer(data={
            'detalles': [
                {'id_producto': 7, 'cantidad': 1, 'precio_unitario': '15.50'},
                {'id_producto': 7, 'cantidad': 2, 'precio_unitario': '20.00'},
            ],
        })

        self.assertFalse(serializer.is_valid())

    def test_serializa_compra_con_detalle_y_nombre_del_producto(self):
        producto = SimpleNamespace(nombre='Cera')
        detalle = SimpleNamespace(
            id_detalle_compra=4,
            id_producto_id=7,
            id_producto=producto,
            cantidad=2,
            precio_unitario=Decimal('15.50'),
            importe=Decimal('31.00'),
            subtotal=Decimal('31.00'),
        )
        compra = SimpleNamespace(
            id_compra=2,
            fecha=datetime(2026, 11, 23, 12, tzinfo=timezone.utc),
            total=Decimal('31.00'),
            detallescompras_set=[detalle],
        )

        self.assertEqual(CompraSerializer(compra).data, {
            'id_compra': 2,
            'fecha': '2026-11-23T09:00:00-03:00',
            'total': '31.00',
            'detalles': [{
                'id_detalle_compra': 4,
                'id_producto': 7,
                'producto_nombre': 'Cera',
                'cantidad': 2,
                'precio_unitario': '15.50',
                'importe': '31.00',
                'subtotal': '31.00',
            }],
        })

    def test_crea_detalle_calcula_importe_y_actualiza_stock_en_transaccion(self):
        producto = SimpleNamespace(id_producto=7, stock_actual=3, save=Mock())
        productos = Mock()
        productos.in_bulk.return_value = {7: producto}
        compra = Mock()

        with (
            patch('compras.api.serializer.transaction.atomic'),
            patch('compras.api.serializer.Productos.objects.select_for_update') as bloquear_productos,
            patch('compras.api.serializer.Compras.objects.create', return_value=compra) as crear_compra,
            patch('compras.api.serializer.DetallesCompras.objects.create') as crear_detalle,
        ):
            bloquear_productos.return_value = productos
            CompraCreateSerializer().create({
                'detalles': [{
                    'id_producto': 7,
                    'cantidad': 2,
                    'precio_unitario': Decimal('15.50'),
                }],
            })

        crear_compra.assert_called_once()
        self.assertEqual(crear_compra.call_args.kwargs['total'], Decimal('31.00'))
        self.assertEqual(crear_detalle.call_args.kwargs['importe'], Decimal('31.00'))
        self.assertEqual(crear_detalle.call_args.kwargs['subtotal'], Decimal('31.00'))
        self.assertEqual(producto.stock_actual, 5)
        producto.save.assert_called_once_with(update_fields=['stock_actual'])
