from contextlib import nullcontext
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from empleados.models import Empleados
from turnos.api.horarios import es_dia_habil, es_reservable


class HorariosReservaTests(SimpleTestCase):
    def setUp(self):
        self.ahora = timezone.make_aware(datetime(2026, 11, 26, 17, 0))

    def test_margen_minimo_de_cinco_minutos(self):
        dia = date(2026, 11, 26)
        self.assertFalse(es_reservable(dia, time(16, 59), ahora=self.ahora))
        self.assertFalse(es_reservable(dia, time(17, 4), ahora=self.ahora))
        self.assertTrue(es_reservable(dia, time(17, 5), ahora=self.ahora))
        self.assertTrue(
            es_reservable(dia + timedelta(days=1), time(9, 0), ahora=self.ahora)
        )

    def test_domingos_estan_cerrados(self):
        self.assertFalse(es_dia_habil(date(2026, 11, 29)))
        self.assertTrue(es_dia_habil(date(2026, 11, 28)))


class TurnosApiTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()
        self.dia = timezone.localdate() + timedelta(days=2)

    def test_disponibilidad_retorna_cada_horario_candidato(self):
        occupied_query = Mock()
        occupied_query.values_list.return_value = [
            (self.dia, time(10, 0)),
        ]
        with (
            patch('turnos.api.view.Empleados.objects.filter') as employees,
            patch('turnos.api.view.Turnos.objects.filter', return_value=occupied_query),
        ):
            employees.return_value.exists.return_value = True
            response = self.client.get(
                '/api/turnos/disponibilidad/',
                {
                    'empleado': 7,
                    'desde': self.dia.isoformat(),
                    'hasta': self.dia.isoformat(),
                    'horas': ['09:00', '10:00'],
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['slots'],
            [
                {
                    'fecha': self.dia.isoformat(),
                    'hora': '09:00',
                    'estado': 'disponible',
                    'disponible': True,
                    'motivo': None,
                },
                {
                    'fecha': self.dia.isoformat(),
                    'hora': '10:00',
                    'estado': 'ocupado',
                    'disponible': False,
                    'motivo': 'ocupado',
                },
            ],
        )

    def test_disponibilidad_marca_horarios_pasados_como_no_disponibles(self):
        occupied_query = Mock()
        occupied_query.values_list.return_value = []
        limite = timezone.make_aware(datetime(2026, 11, 26, 17, 0))
        with (
            patch('turnos.api.view.Empleados.objects.filter') as employees,
            patch('turnos.api.view.Turnos.objects.filter', return_value=occupied_query),
            patch('turnos.api.view.hora_limite', return_value=limite),
        ):
            employees.return_value.exists.return_value = True
            response = self.client.get(
                '/api/turnos/disponibilidad/',
                {
                    'empleado': 7,
                    'desde': '2026-11-26',
                    'hasta': '2026-11-26',
                    'horas': ['16:00', '17:10'],
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['slots'],
            [
                {
                    'fecha': '2026-11-26',
                    'hora': '16:00',
                    'estado': 'ocupado',
                    'disponible': False,
                    'motivo': 'hora_no_disponible',
                },
                {
                    'fecha': '2026-11-26',
                    'hora': '17:10',
                    'estado': 'disponible',
                    'disponible': True,
                    'motivo': None,
                },
            ],
        )

    def test_disponibilidad_marca_el_domingo_como_cerrado(self):
        occupied_query = Mock()
        occupied_query.values_list.return_value = []
        with (
            patch('turnos.api.view.Empleados.objects.filter') as employees,
            patch('turnos.api.view.Turnos.objects.filter', return_value=occupied_query),
        ):
            employees.return_value.exists.return_value = True
            response = self.client.get(
                '/api/turnos/disponibilidad/',
                {
                    'empleado': 7,
                    'desde': '2026-11-29',
                    'hasta': '2026-11-29',
                    'horas': ['10:00'],
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['slots'],
            [{
                'fecha': '2026-11-29',
                'hora': '10:00',
                'estado': 'ocupado',
                'disponible': False,
                'motivo': 'dia_cerrado',
            }],
        )

    def test_reserva_rechaza_domingo_sin_crear_cliente(self):
        with (
            patch('turnos.api.view.Clientes.objects.get_or_create') as get_or_create,
            patch('turnos.api.view.Turnos.objects.create') as crear,
        ):
            response = self.client.post(
                '/api/turnos/reservas/',
                {
                    'empleado': 7,
                    'fecha': '2026-11-29',
                    'hora': '10:00',
                    'nombre': 'Ada',
                    'apellido': 'Lovelace',
                    'telefono': '555123',
                },
                format='json',
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['error']['code'], 'dia_no_habil')
        get_or_create.assert_not_called()
        crear.assert_not_called()

    def test_reserva_rechaza_horario_ocupado_sin_crear_cliente(self):
        occupied_query = Mock()
        occupied_query.exists.return_value = True
        employee = SimpleNamespace(pk=7)
        with (
            patch('turnos.api.view.transaction.atomic', return_value=nullcontext()),
            patch(
                'turnos.api.view.Empleados.objects.select_for_update'
            ) as employees,
            patch('turnos.api.view.Turnos.objects.filter', return_value=occupied_query),
            patch('turnos.api.view.Clientes.objects.get_or_create') as get_or_create,
        ):
            employees.return_value.get.return_value = employee
            response = self.client.post(
                '/api/turnos/reservas/',
                {
                    'empleado': 7,
                    'fecha': self.dia.isoformat(),
                    'hora': '10:00',
                    'nombre': 'Ada',
                    'apellido': 'Lovelace',
                    'telefono': '555123',
                },
                format='json',
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['error']['code'], 'slot_unavailable')
        get_or_create.assert_not_called()

    def test_reserva_rechaza_horario_sin_margen_sin_crear_cliente(self):
        with (
            patch('turnos.api.view.es_reservable', return_value=False),
            patch('turnos.api.view.Clientes.objects.get_or_create') as get_or_create,
            patch('turnos.api.view.Turnos.objects.create') as crear,
        ):
            response = self.client.post(
                '/api/turnos/reservas/',
                {
                    'empleado': 7,
                    'fecha': self.dia.isoformat(),
                    'hora': '10:00',
                    'nombre': 'Ada',
                    'apellido': 'Lovelace',
                    'telefono': '555123',
                },
                format='json',
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['error']['code'], 'hora_no_disponible')
        get_or_create.assert_not_called()
        crear.assert_not_called()

    def test_reserva_reutiliza_cliente_y_crea_turno_pendiente(self):
        occupied_query = Mock()
        occupied_query.exists.return_value = False
        employee = SimpleNamespace(pk=7)
        customer = SimpleNamespace(pk=12)
        booking = SimpleNamespace(
            pk=34,
            fecha=self.dia,
            hora=time(10, 0),
            estado='pendiente',
        )
        with (
            patch(
                'turnos.api.view.transaction.atomic',
                return_value=nullcontext(),
            ) as atomic,
            patch(
                'turnos.api.view.Empleados.objects.select_for_update'
            ) as employees,
            patch('turnos.api.view.Turnos.objects.filter', return_value=occupied_query),
            patch(
                'turnos.api.view.Clientes.objects.get_or_create',
                return_value=(customer, False),
            ) as get_or_create,
            patch('turnos.api.view.Turnos.objects.create', return_value=booking),
        ):
            employees.return_value.get.return_value = employee
            response = self.client.post(
                '/api/turnos/reservas/',
                {
                    'empleado': 7,
                    'fecha': self.dia.isoformat(),
                    'hora': '10:00',
                    'nombre': 'Ada',
                    'apellido': 'Lovelace',
                    'telefono': '555123',
                },
                format='json',
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['cliente'], 12)
        self.assertEqual(response.data['estado'], 'pendiente')
        atomic.assert_called_once_with()
        employees.assert_called_once_with()
        get_or_create.assert_called_once_with(
            telefono='555123',
            defaults={
                'nombre': 'Ada',
                'apellido': 'Lovelace',
            },
        )

    def test_reserva_rechaza_datos_invalidos_con_error_consistente(self):
        response = self.client.post(
            '/api/turnos/reservas/',
            {'empleado': 'no-es-id'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error']['code'], 'validation_error')

    def test_reserva_informa_empleado_inexistente(self):
        with (
            patch('turnos.api.view.transaction.atomic', return_value=nullcontext()),
            patch(
                'turnos.api.view.Empleados.objects.select_for_update'
            ) as employees,
        ):
            employees.return_value.get.side_effect = Empleados.DoesNotExist
            response = self.client.post(
                '/api/turnos/reservas/',
                {
                    'empleado': 999,
                    'fecha': self.dia.isoformat(),
                    'hora': '10:00',
                    'nombre': 'Ada',
                    'apellido': 'Lovelace',
                    'telefono': '555123',
                },
                format='json',
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error']['code'], 'employee_not_found')
