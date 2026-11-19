from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from empleados.management.commands.crear_roles import ROLES
from empleados.api.view import LiquidacionesSemanalesViewSet
from empleados.models import Empleados
from rest_framework.test import APIClient


class RolesConfigurationTests(SimpleTestCase):
    def test_roles_configurados(self):
        self.assertEqual(set(ROLES), {'Administrador', 'Cajero', 'Barbero'})

    def test_cajero_puede_modificar_modulos_de_caja_pero_solo_ver_productos(self):
        permisos = set(ROLES['Cajero'])

        self.assertIn('add_clientes', permisos)
        self.assertIn('change_turnos', permisos)
        self.assertIn('add_ventas', permisos)
        self.assertIn('change_cajas', permisos)
        self.assertIn('add_movimientoscajas', permisos)
        self.assertIn('add_servicios', permisos)
        self.assertIn('change_servicios', permisos)
        self.assertIn('view_productos', permisos)
        self.assertNotIn('add_productos', permisos)
        self.assertNotIn('change_productos', permisos)
        self.assertFalse(any(codename.startswith('delete_') for codename in permisos))

    def test_barbero_puede_agregar_turnos_ver_servicios_y_liquidaciones(self):
        permisos = set(ROLES['Barbero'])

        self.assertIn('view_turnos', permisos)
        self.assertIn('add_turnos', permisos)
        self.assertIn('view_servicios', permisos)
        self.assertIn('view_liquidacionessemanales', permisos)
        self.assertNotIn('view_empleados', permisos)
        self.assertNotIn('change_turnos', permisos)

    def test_api_usa_token_authentication(self):
        self.assertEqual(
            settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'],
            ('rest_framework.authentication.TokenAuthentication',),
        )


class EmpleadosModelTests(SimpleTestCase):
    def test_usuario_empleado_apunta_al_usuario_de_django(self):
        campo_usuario = Empleados._meta.get_field('id_usuario')

        self.assertIs(campo_usuario.remote_field.model, get_user_model())


class AuthenticationApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='cajero',
            password='ClaveSegura123!',
        )
        self.client = APIClient()

    def test_usuario_sin_token_no_puede_acceder_a_empleados(self):
        response = self.client.get('/api/empleados/')

        self.assertEqual(response.status_code, 401)

    def test_cajero_autenticado_no_puede_administrar_empleados(self):
        call_command('crear_roles')
        Group.objects.get(name='Cajero').user_set.add(self.user)
        token_response = self.client.post(
            '/api/auth/token/',
            {'username': 'cajero', 'password': 'ClaveSegura123!'},
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token_response.data['token']}"
        )

        response = self.client.get('/api/empleados/')

        self.assertEqual(response.status_code, 403)

    def test_login_emite_token_y_perfil_devuelve_grupo(self):
        Group.objects.create(name='Cajero').user_set.add(self.user)
        token_response = self.client.post(
            '/api/auth/token/',
            {'username': 'cajero', 'password': 'ClaveSegura123!'},
            format='json',
        )

        self.assertEqual(token_response.status_code, 200)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token_response.data['token']}"
        )
        profile_response = self.client.get('/api/auth/me/')

        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.data['groups'], ['Cajero'])
        self.assertEqual(profile_response.data['username'], 'cajero')

    def test_logout_revoca_el_token_actual(self):
        token_response = self.client.post(
            '/api/auth/token/',
            {'username': 'cajero', 'password': 'ClaveSegura123!'},
            format='json',
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token_response.data['token']}"
        )

        response = self.client.post('/api/auth/logout/')

        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)


class RoleCommandTests(TestCase):
    def test_comando_crea_grupos_compartidos_con_permisos_segun_rol(self):
        call_command('crear_roles')

        administrador = Group.objects.get(name='Administrador')
        cajero = Group.objects.get(name='Cajero')
        barbero = Group.objects.get(name='Barbero')

        self.assertTrue(administrador.permissions.exists())
        self.assertTrue(cajero.permissions.filter(codename='add_ventas').exists())
        self.assertFalse(cajero.permissions.filter(codename='add_productos').exists())
        self.assertTrue(barbero.permissions.filter(codename='add_turnos').exists())
        self.assertTrue(
            barbero.permissions.filter(codename='view_liquidacionessemanales').exists()
        )

        cajero_usuario = get_user_model().objects.create_user(
            username='cajero',
            password='ClaveSegura123!',
        )
        cajero.user_set.add(cajero_usuario)
        self.assertTrue(cajero_usuario.has_perm('ventas.add_ventas'))
        self.assertFalse(cajero_usuario.has_perm('productos.add_productos'))

    def test_comando_migra_usuarios_del_grupo_dueno_a_administrador(self):
        usuario = get_user_model().objects.create_user(
            username='administrador',
            password='ClaveSegura123!',
        )
        Group.objects.create(name='Dueño').user_set.add(usuario)

        call_command('crear_roles')

        self.assertTrue(
            usuario.groups.filter(name='Administrador').exists()
        )
        self.assertFalse(Group.objects.filter(name='Dueño').exists())


class LiquidacionesQuerysetTests(SimpleTestCase):
    def test_barbero_solo_consulta_liquidaciones_asociadas_a_su_usuario(self):
        user = SimpleNamespace(is_superuser=False, groups=Mock())
        user.groups.filter.return_value.exists.return_value = False
        queryset = Mock()
        view = LiquidacionesSemanalesViewSet()
        view.request = SimpleNamespace(user=user)

        with patch(
            'empleados.api.view.LiquidacionesSemanales.objects.all',
            return_value=queryset,
        ):
            result = view.get_queryset()

        self.assertIs(result, queryset.filter.return_value)
        queryset.filter.assert_called_once_with(id_empleado__id_usuario=user)

    def test_administrador_puede_consultar_todas_las_liquidaciones(self):
        user = SimpleNamespace(is_superuser=False, groups=Mock())
        user.groups.filter.return_value.exists.return_value = True
        queryset = Mock()
        view = LiquidacionesSemanalesViewSet()
        view.request = SimpleNamespace(user=user)

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

    def test_lista_administrativa_de_empleados_sigue_protegida(self):
        response = APIClient().get('/api/empleados/')

        self.assertEqual(response.status_code, 401)
