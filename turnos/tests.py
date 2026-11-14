from contextlib import nullcontext
from datetime import date, time
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from rest_framework.test import APIClient

from empleados.models import Empleados


class TurnosApiTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()

    def test_disponibilidad_retorna_cada_horario_candidato(self):
        occupied_query = Mock()
        occupied_query.values_list.return_value = [
            (date(2026, 11, 20), time(10, 0)),
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
                    'desde': '2026-11-20',
                    'hasta': '2026-11-20',
                    'horas': ['09:00', '10:00'],
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['slots'],
            [
                {
                    'fecha': '2026-11-20',
                    'hora': '09:00',
                    'estado': 'disponible',
                    'disponible': True,
                },
                {
                    'fecha': '2026-11-20',
                    'hora': '10:00',
                    'estado': 'ocupado',
                    'disponible': False,
                },
            ],
        )

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
                    'fecha': '2026-11-20',
                    'hora': '10:00',
                    'nombre': 'Ada',
                    'apellido': 'Lovelace',
                    'telefono': '555123',
                    'email': 'ada@example.com',
                },
                format='json',
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['error']['code'], 'slot_unavailable')
        get_or_create.assert_not_called()

    def test_reserva_reutiliza_cliente_y_crea_turno_pendiente(self):
        occupied_query = Mock()
        occupied_query.exists.return_value = False
        employee = SimpleNamespace(pk=7)
        customer = SimpleNamespace(pk=12)
        booking = SimpleNamespace(
            pk=34,
            fecha=date(2026, 11, 20),
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
                    'fecha': '2026-11-20',
                    'hora': '10:00',
                    'nombre': 'Ada',
                    'apellido': 'Lovelace',
                    'telefono': '555123',
                    'email': 'ada@example.com',
                },
                format='json',
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['cliente'], 12)
        self.assertEqual(response.data['estado'], 'pendiente')
        atomic.assert_called_once_with()
        employees.assert_called_once_with()
        get_or_create.assert_called_once_with(
            email='ada@example.com',
            defaults={
                'nombre': 'Ada',
                'apellido': 'Lovelace',
                'telefono': '555123',
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
                    'fecha': '2026-11-20',
                    'hora': '10:00',
                    'nombre': 'Ada',
                    'apellido': 'Lovelace',
                    'telefono': '555123',
                    'email': 'ada@example.com',
                },
                format='json',
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error']['code'], 'employee_not_found')
