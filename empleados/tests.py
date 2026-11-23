from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from empleados.api.view import LiquidacionesSemanalesViewSet
from empleados.models import Empleados
from rest_framework.test import APIClient

class EmpleadosModelTests(SimpleTestCase):
    def test_empleado_no_tiene_vinculo_con_usuario(self):
        self.assertFalse(
            any(field.name == 'id_usuario' for field in Empleados._meta.get_fields())
        )


class LiquidacionesQuerysetTests(SimpleTestCase):
    def test_consulta_liquidaciones_sin_filtro_de_usuario(self):
        queryset = Mock()
        view = LiquidacionesSemanalesViewSet()

        with patch(
            'empleados.api.view.LiquidacionesSemanales.objects.all',
            return_value=queryset,
        ):
            result = view.get_queryset()

        self.assertIs(result, queryset)
        queryset.filter.assert_not_called()


class PublicBarberosApiTests(SimpleTestCase):
    def test_barberos_son_publicos_y_solo_exponen_datos_necesarios(self):
        empleados = [
            SimpleNamespace(
                id_empleado=7,
                nombre='Ada',
                apellido='Lovelace',
                foto_empleado='/media/ada.jpg',
                dni='dato-privado',
                porcentaje_comision=50,
            )
        ]
        client = APIClient()

        with patch('empleados.api.view.Empleados.objects.filter') as filtrar:
            filtrar.return_value.order_by.return_value = empleados
            response = client.get('/api/barberos/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            [{
                'id_empleado': 7,
                'nombre': 'Ada',
                'apellido': 'Lovelace',
                'foto_empleado': '/media/ada.jpg',
            }],
        )
        filtrar.assert_called_once_with(id_rol__nombre='Barbero')

    def test_lista_administrativa_de_empleados_es_publica(self):
        with patch(
            'empleados.api.view.EmpleadosViewSet.queryset',
            [],
        ):
            response = APIClient().get('/api/empleados/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
