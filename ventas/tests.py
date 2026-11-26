from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient

from ventas.api.views import VentasViewSet

DATOS_ANULACION = {
    'motivo': 'Motivo válido de anulación',
    'usuario': 'cajero',
    'contrasena': 'clave',
}


class CrearTicketCajaTests(SimpleTestCase):
    @patch('ventas.api.views.Cajas.objects.filter')
    def test_crear_ticket_sin_caja_devuelve_409(self, filtrar):
        filtrar.return_value.exists.return_value = False

        response = APIClient().post(
            '/api/ventas/crear-ticket/',
            {},
            format='json',
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['detail'], 'No hay una caja abierta.')


class VentasMetodosTests(SimpleTestCase):
    def test_no_permite_eliminar_ventas(self):
        response = APIClient().delete('/api/ventas/1/')

        self.assertEqual(response.status_code, 405)
        self.assertNotIn('delete', VentasViewSet.http_method_names)

    def test_no_permite_editar_ventas(self):
        response = APIClient().patch(
            '/api/ventas/1/',
            {'subtotal': '1.00'},
            format='json',
        )

        self.assertEqual(response.status_code, 405)
        self.assertNotIn('patch', VentasViewSet.http_method_names)
        self.assertNotIn('put', VentasViewSet.http_method_names)

    def test_no_permite_crear_venta_directa(self):
        response = APIClient().post('/api/ventas/', {}, format='json')

        self.assertEqual(response.status_code, 405)


class AnularVentaTests(SimpleTestCase):
    def test_anular_exige_motivo_usuario_y_contrasena(self):
        response = APIClient().post(
            '/api/ventas/1/anular/',
            {},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('motivo', response.data)
        self.assertIn('usuario', response.data)
        self.assertIn('contrasena', response.data)

    @patch(
        'ventas.api.views.autenticar_cajero',
        side_effect=PermissionDenied('Usuario o contraseña incorrectos.'),
    )
    def test_anular_con_credenciales_invalidas_devuelve_403(self, _):
        response = APIClient().post(
            '/api/ventas/1/anular/',
            DATOS_ANULACION,
            format='json',
        )

        self.assertEqual(response.status_code, 403)

    @patch('ventas.api.views.autenticar_cajero')
    @patch('ventas.api.views.Ventas.objects.select_for_update')
    def test_anular_venta_ya_anulada_devuelve_409(
        self,
        select_for_update,
        autenticar,
    ):
        autenticar.return_value = SimpleNamespace(pk=1, id_user_id=None)
        select_for_update.return_value.filter.return_value.first.return_value = (
            SimpleNamespace(anulada=True, estado=True)
        )

        with patch('ventas.api.views.transaction.atomic', nullcontext):
            response = APIClient().post(
                '/api/ventas/1/anular/',
                DATOS_ANULACION,
                format='json',
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['detail'], 'La venta ya está anulada.')

    @patch('ventas.api.views.autenticar_cajero')
    @patch('ventas.api.views.Ventas.objects.select_for_update')
    def test_no_se_anula_un_ticket_pendiente(
        self,
        select_for_update,
        autenticar,
    ):
        autenticar.return_value = SimpleNamespace(pk=1, id_user_id=None)
        select_for_update.return_value.filter.return_value.first.return_value = (
            SimpleNamespace(anulada=False, estado=False)
        )

        with patch('ventas.api.views.transaction.atomic', nullcontext):
            response = APIClient().post(
                '/api/ventas/1/anular/',
                DATOS_ANULACION,
                format='json',
            )

        self.assertEqual(response.status_code, 409)


class CancelarVentaTests(SimpleTestCase):
    def test_cancelar_exige_motivo(self):
        response = APIClient().post(
            '/api/ventas/1/cancelar/',
            {},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('motivo', response.data)

    @patch('ventas.api.views.Cajas.objects.select_related')
    @patch('ventas.api.views.Ventas.objects.select_for_update')
    def test_cancelar_sin_caja_abierta_devuelve_409(
        self,
        select_for_update,
        select_related,
    ):
        select_for_update.return_value.filter.return_value.first.return_value = (
            SimpleNamespace(anulada=False, estado=False)
        )
        select_related.return_value.filter.return_value.order_by.return_value.first.return_value = None

        with patch('ventas.api.views.transaction.atomic', nullcontext):
            response = APIClient().post(
                '/api/ventas/1/cancelar/',
                {'motivo': 'Ticket duplicado en el mostrador'},
                format='json',
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['detail'], 'No hay una caja abierta.')
