from decimal import Decimal
from datetime import date
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from django.urls import Resolver404, resolve
from rest_framework.test import APIClient

from api.dashboard import calcular_resumen_dashboard, obtener_resumen_dashboard

class AdminLoginRemovalTests(SimpleTestCase):
    def test_login_and_session_endpoints_are_no_longer_available(self):
        for path in (
            '/api/auth/csrf/',
            '/api/auth/login/',
            '/api/auth/me/',
            '/api/auth/logout/',
        ):
            with self.subTest(path=path):
                with self.assertRaises(Resolver404):
                    resolve(path)


class DashboardAdministradorApiTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()

    def test_dashboard_summary_route_is_registered(self):
        match = resolve('/api/dashboard/administrador/')

        self.assertEqual(match.url_name, 'dashboard-administrador')

    @patch('api.views.obtener_resumen_dashboard')
    def test_dashboard_uses_validated_dates_and_returns_aggregates(self, obtener):
        esperado = {'turnos_hoy': {'total': 4, 'pendientes': 1}}
        obtener.return_value = esperado

        with patch('api.views.timezone.localdate', return_value=date(2026, 11, 20)):
            response = self.client.get(
                '/api/dashboard/administrador/',
                {
                    'fecha_caja': '2026-11-19',
                    'fecha_barberos': '2026-11-18',
                    'fecha_cortes': '2026-11-17',
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, esperado)
        obtener.assert_called_once_with(
            fecha_hoy=date(2026, 11, 20),
            fecha_caja=date(2026, 11, 19),
            fecha_barberos=date(2026, 11, 18),
            fecha_cortes=date(2026, 11, 17),
        )

    def test_dashboard_rejects_invalid_date_filters(self):
        response = self.client.get(
            '/api/dashboard/administrador/',
            {'fecha_caja': 'ayer'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('fecha_caja', response.data)

    def test_summary_uses_real_domains_and_selected_chart_dates(self):
        resumen = calcular_resumen_dashboard(
            fecha_hoy='2026-11-20',
            fecha_caja='2026-11-19',
            fecha_barberos='2026-11-18',
            fecha_cortes='2026-11-17',
            turnos_hoy=[
                {'estado': 'pendiente'},
                {'estado': 'finalizado'},
            ],
            turnos_express_hoy=[{'estado': 'pendiente'}],
            movimientos_caja_hoy=[
                {'tipo_movimiento': 'cobro', 'total': Decimal('12500.00')},
                {'tipo_movimiento': 'ingreso', 'total': Decimal('500.00')},
                {'tipo_movimiento': 'egreso', 'total': Decimal('900.00')},
                {'tipo_movimiento': 'apertura', 'total': Decimal('20000.00')},
            ],
            movimientos_caja_fecha=[
                {'tipo_movimiento': 'cobro', 'total': Decimal('7000.00')},
                {'tipo_movimiento': 'egreso', 'total': Decimal('250.00')},
            ],
            tickets_abiertos=4,
            liquidaciones_pendientes=2,
            barberos=[
                {'id_empleado': 1, 'nombre': 'Ada', 'apellido': 'Lovelace'},
                {'id_empleado': 2, 'nombre': 'Grace', 'apellido': 'Hopper'},
            ],
            asistencias=[
                {'id_empleado_id': 1, 'estado': 'presente'},
                {'id_empleado_id': 2, 'estado': 'ausente'},
            ],
            turnos_cortes=[
                {'estado': 'finalizado'},
                {'estado': 'pendiente'},
            ],
            turnos_express_cortes=[
                {'estado': 'completado'},
                {'estado': 'en curso'},
            ],
        )

        self.assertEqual(resumen['turnos_hoy'], {'total': 3, 'pendientes': 2})
        self.assertEqual(resumen['caja_hoy'], '13000.00')
        self.assertEqual(resumen['tickets_abiertos'], 4)
        self.assertEqual(resumen['liquidaciones_pendientes'], 2)
        self.assertEqual(
            resumen['caja'],
            {'fecha': '2026-11-19', 'ingresos': '7000.00'},
        )
        self.assertEqual(
            resumen['asistencia'],
            {
                'fecha': '2026-11-18',
                'presentes': 1,
                'total': 2,
                'barberos': [
                    {'id': 1, 'nombre': 'Ada Lovelace', 'presente': True},
                    {'id': 2, 'nombre': 'Grace Hopper', 'presente': False},
                ],
            },
        )
        self.assertEqual(resumen['cortes'], {'fecha': '2026-11-17', 'realizados': 2})

    def test_summary_returns_zeros_and_empty_roster_without_records(self):
        resumen = calcular_resumen_dashboard(
            fecha_hoy='2026-11-20',
            fecha_caja='2026-11-19',
            fecha_barberos='2026-11-18',
            fecha_cortes='2026-11-17',
            turnos_hoy=[],
            turnos_express_hoy=[],
            movimientos_caja_hoy=[],
            movimientos_caja_fecha=[],
            tickets_abiertos=0,
            liquidaciones_pendientes=0,
            barberos=[],
            asistencias=[],
            turnos_cortes=[],
            turnos_express_cortes=[],
        )

        self.assertEqual(resumen['turnos_hoy'], {'total': 0, 'pendientes': 0})
        self.assertEqual(resumen['caja_hoy'], '0.00')
        self.assertEqual(resumen['tickets_abiertos'], 0)
        self.assertEqual(resumen['liquidaciones_pendientes'], 0)
        self.assertEqual(
            resumen['asistencia'],
            {'fecha': '2026-11-18', 'presentes': 0, 'total': 0, 'barberos': []},
        )
        self.assertEqual(resumen['cortes'], {'fecha': '2026-11-17', 'realizados': 0})

    def test_dashboard_service_reads_each_database_source(self):
        def resultado(filas):
            queryset = Mock()
            queryset.values.return_value = filas
            return queryset

        with (
            patch('api.dashboard.Turnos.objects.filter') as turnos,
            patch('api.dashboard.TurnosExpress.objects.filter') as express,
            patch('api.dashboard.MovimientosCajas.objects.annotate') as movimientos,
            patch('api.dashboard.Ventas.objects.filter') as ventas,
            patch('api.dashboard.LiquidacionesSemanales.objects.filter') as liquidaciones,
            patch('api.dashboard.Empleados.objects.filter') as empleados,
            patch('api.dashboard.RegistrosAsistencias.objects.filter') as asistencias,
        ):
            turnos.side_effect = [
                resultado([{'estado': 'pendiente', 'id_empleado_id': 1}]),
                resultado([{'estado': 'finalizado', 'id_empleado_id': 1}]),
            ]
            express.side_effect = [
                resultado([{'estado': 'cancelado', 'id_empleado_id': 2}]),
                resultado([{'estado': 'completado', 'id_empleado_id': 2}]),
            ]
            movimientos_queryset = Mock()
            movimientos_queryset.filter.side_effect = [
                resultado([
                    {'tipo_movimiento': 'cobro', 'total': Decimal('12500')},
                ]),
                resultado([
                    {'tipo_movimiento': 'ingreso', 'total': Decimal('7000')},
                ]),
            ]
            movimientos.return_value = movimientos_queryset
            ventas.return_value.count.return_value = 4
            liquidaciones.return_value.count.return_value = 2
            empleados.return_value.values.return_value = [
                {'id_empleado': 1, 'nombre': 'Ada', 'apellido': 'Lovelace'},
                {'id_empleado': 2, 'nombre': 'Grace', 'apellido': 'Hopper'},
            ]
            asistencias.return_value.values.return_value = [
                {'id_empleado_id': 1, 'estado': 'presente'},
            ]

            resumen = obtener_resumen_dashboard(
                fecha_hoy=date(2026, 11, 20),
                fecha_caja=date(2026, 11, 19),
                fecha_barberos=date(2026, 11, 18),
                fecha_cortes=date(2026, 11, 17),
            )

        self.assertEqual(resumen['turnos_hoy'], {'total': 2, 'pendientes': 1})
        self.assertEqual(resumen['caja_hoy'], '12500.00')
        self.assertEqual(resumen['tickets_abiertos'], 4)
        self.assertEqual(resumen['liquidaciones_pendientes'], 2)
        self.assertEqual(resumen['caja']['ingresos'], '7000.00')
        self.assertEqual(resumen['asistencia']['presentes'], 1)
        self.assertEqual(resumen['cortes']['realizados'], 2)
