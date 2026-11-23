from types import SimpleNamespace
from unittest.mock import Mock, patch
from contextlib import nullcontext

from django.test import SimpleTestCase
from django.urls import reverse
from django.contrib.auth.hashers import check_password, make_password
from rest_framework import serializers

from empleados.api import serializer as empleado_serializer
from empleados.api.serializer import EmpleadosSerializer
from empleados.api.view import (
    EmpleadosViewSet,
    GruposAPIView,
    LiquidacionesSemanalesViewSet,
    RolesAPIView,
)
from empleados.models import EmpleadoCuenta, Empleados
from rest_framework.test import APIClient


class EmpleadoCuentaInputTests(SimpleTestCase):
    def test_crear_cuenta_requiere_usuario_contrasena_y_grupo(self):
        serializer = EmpleadosSerializer()

        with self.assertRaises(serializers.ValidationError):
            serializer.validate({'usuario': 'ana'})

    def test_empleado_sin_cuenta_acepta_campos_de_cuenta_vacios(self):
        serializer = EmpleadosSerializer()

        result = serializer.validate({
            'usuario': '',
            'contrasena': '',
            'grupo_usuario': '',
        })

        self.assertEqual(result['usuario'], '')
        self.assertEqual(result['contrasena'], '')
        self.assertEqual(result['grupo_usuario'], '')

    def test_patch_con_campos_vacios_conserva_la_cuenta(self):
        usuario = SimpleNamespace(
            username='ana',
            password=make_password('ClaveAnterior!234'),
            save=Mock(),
        )
        cuenta = SimpleNamespace(usuario=usuario)
        empleado = SimpleNamespace(cuenta=cuenta)
        serializer = EmpleadosSerializer(instance=empleado, partial=True)

        with (
            patch.object(
                serializers.ModelSerializer,
                'update',
                return_value=empleado,
            ),
            patch.object(empleado_serializer.transaction, 'atomic', nullcontext),
        ):
            serializer.update(empleado, {
                'usuario': '',
                'contrasena': '',
                'grupo_usuario': '',
            })

        self.assertEqual(usuario.username, 'ana')
        self.assertTrue(check_password('ClaveAnterior!234', usuario.password))
        usuario.save.assert_not_called()

    def test_patch_con_contrasena_almacena_hash(self):
        usuario = SimpleNamespace(
            username='ana',
            password='',
            set_password=lambda password: setattr(
                usuario,
                'password',
                make_password(password),
            ),
            save=Mock(),
        )
        empleado = SimpleNamespace(cuenta=SimpleNamespace(usuario=usuario))
        serializer = EmpleadosSerializer(instance=empleado, partial=True)

        with (
            patch.object(
                serializers.ModelSerializer,
                'update',
                return_value=empleado,
            ),
            patch.object(empleado_serializer.transaction, 'atomic', nullcontext),
        ):
            serializer.update(empleado, {'contrasena': 'ClaveNueva!567'})

        self.assertNotEqual(usuario.password, 'ClaveNueva!567')
        self.assertTrue(check_password('ClaveNueva!567', usuario.password))
        usuario.save.assert_called_once_with(update_fields=['password'])

    def test_respuesta_de_cuenta_no_incluye_contrasena(self):
        usuario = SimpleNamespace(
            get_username=lambda: 'ana',
            groups=Mock(),
        )
        usuario.groups.all.return_value = [SimpleNamespace(name='Barberos')]
        empleado = SimpleNamespace(
            cuenta=SimpleNamespace(usuario=usuario),
        )

        resultado = EmpleadosSerializer().get_cuenta(empleado)

        self.assertEqual(resultado, {'usuario': 'ana', 'grupo': 'Barberos'})
        self.assertNotIn('contrasena', resultado)


class EmpleadosModelTests(SimpleTestCase):
    def test_empleado_no_tiene_vinculo_con_usuario(self):
        self.assertFalse(
            any(field.name == 'id_usuario' for field in Empleados._meta.get_fields())
        )

    def test_eliminar_empleado_desactiva_su_usuario(self):
        usuario = SimpleNamespace(is_active=True, save=Mock())
        empleado = SimpleNamespace(
            delete=Mock(),
        )

        with (
            patch.object(empleado_serializer.transaction, 'atomic', nullcontext),
            patch('empleados.api.view.EmpleadoCuenta.objects.select_related') as cuentas,
        ):
            cuentas.return_value.filter.return_value.first.return_value = SimpleNamespace(
                usuario=usuario,
            )
            EmpleadosViewSet().perform_destroy(empleado)

        self.assertFalse(usuario.is_active)
        usuario.save.assert_called_once_with(update_fields=['is_active'])
        empleado.delete.assert_called_once_with()

    def test_eliminar_empleado_sin_cuenta_no_intenta_desactivar_usuario(self):
        empleado = SimpleNamespace()
        empleado.delete = Mock()

        with (
            patch.object(empleado_serializer.transaction, 'atomic', nullcontext),
            patch('empleados.api.view.EmpleadoCuenta.objects.select_related') as cuentas,
        ):
            cuentas.return_value.filter.return_value.first.return_value = None
            EmpleadosViewSet().perform_destroy(empleado)

        empleado.delete.assert_called_once_with()


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

    def test_lista_administrativa_de_empleados_permite_anonimos(self):
        with patch(
            'empleados.api.view.EmpleadosViewSet.queryset',
            [],
        ):
            response = APIClient().get(reverse('empleados-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

    def test_creacion_de_empleado_no_requiere_autenticacion(self):
        serializer = Mock()
        serializer.data = {'id_empleado': 7}
        with patch.object(EmpleadosViewSet, 'get_serializer', return_value=serializer):
            response = APIClient().post(
                reverse('empleados-list'),
                {'nombre': 'Ada'},
                format='json',
            )

        self.assertEqual(response.status_code, 201)
        serializer.save.assert_called_once_with()

    def test_grupos_de_usuario_se_listan_sin_autenticacion(self):
        client = APIClient()
        with patch.object(
            GruposAPIView,
            'queryset',
            [SimpleNamespace(id=3, name='Barberos')],
        ):
            response = client.get(reverse('grupos-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [{'id': 3, 'name': 'Barberos'}])

    def test_roles_laborales_se_listan_sin_autenticacion(self):
        client = APIClient()
        with patch.object(
            RolesAPIView,
            'queryset',
            [SimpleNamespace(id_rol=2, nombre='Barbero')],
        ):
            response = client.get(reverse('roles-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [{'id_rol': 2, 'nombre': 'Barbero'}])
