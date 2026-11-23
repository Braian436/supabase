from django.test import SimpleTestCase
from django.urls import resolve

from servicios.api.serializer import ServiciosSerializer
from servicios.models import Servicios


class ServiciosApiTests(SimpleTestCase):
    def test_publica_rutas_de_listado_y_detalle(self):
        self.assertEqual(resolve('/api/servicios/').url_name, 'servicios-list')
        self.assertEqual(resolve('/api/servicios/3/').url_name, 'servicios-detail')

    def test_serializa_nombre_descripcion_y_precio(self):
        servicio = Servicios(
            id_servicio=3,
            nombre='Corte clásico',
            descripcion='Corte con tijera',
            precio='12500.00',
        )

        self.assertEqual(ServiciosSerializer(servicio).data, {
            'id_servicio': 3,
            'nombre': 'Corte clásico',
            'descripcion': 'Corte con tijera',
            'precio': '12500.00',
        })
