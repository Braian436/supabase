from types import SimpleNamespace
from unittest.mock import Mock, patch
from contextlib import nullcontext

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from django.contrib.auth.hashers import check_password, make_password
from django.urls import Resolver404, resolve, reverse
from rest_framework import serializers
from rest_framework.test import APIClient

from empleados.api import serializer as empleado_serializer
from empleados.api.serializer import EmpleadosSerializer
from empleados.api.view import (
    EmpleadosViewSet,
    GruposAPIView,
    LiquidacionesSemanalesViewSet,
)
from empleados.models import Empleados


class CuentaEmpleadoInputTests(SimpleTestCase):
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
        empleado = SimpleNamespace(id_user=usuario)
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
        empleado = SimpleNamespace(id_user=usuario)
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
        empleado = SimpleNamespace(id_user=usuario)

        resultado = EmpleadosSerializer().get_cuenta(empleado)

        self.assertEqual(resultado, {'usuario': 'ana', 'grupo': 'Barberos'})
        self.assertNotIn('contrasena', resultado)

    def test_crear_cuenta_asocia_usuario_directamente_al_empleado(self):
        usuario = SimpleNamespace(groups=Mock())
        empleado = SimpleNamespace(id_user=None, save=Mock())
        user_model = Mock()
        user_model.objects.create_user.return_value = usuario

        with (
            patch.object(empleado_serializer, 'get_user_model', return_value=user_model),
            patch.object(empleado_serializer.Group.objects, 'get') as obtener_grupo,
        ):
            obtener_grupo.return_value = SimpleNamespace(name='Barberos')
            EmpleadosSerializer()._guardar_cuenta(
                empleado,
                {
                    'usuario': 'ana',
                    'contrasena': 'ClaveFuerte!234',
                    'grupo_usuario': 'Barberos',
                },
            )

        self.assertIs(empleado.id_user, usuario)
        empleado.save.assert_called_once_with(update_fields=['id_user'])
        usuario.groups.set.assert_called_once()


class EmpleadosModelTests(SimpleTestCase):
    def test_id_user_es_una_relacion_one_to_one_con_el_usuario_de_django(self):
        field = Empleados._meta.get_field('id_user')

        self.assertTrue(field.one_to_one)
        self.assertIs(field.remote_field.model, get_user_model())
        self.assertEqual(field.db_column, 'id_user')

    def test_representacion_del_empleado_no_depende_de_rol(self):
        empleado = Empleados(
            nombre='Ada',
            apellido='Lovelace',
            dni='123',
        )

        self.assertEqual(str(empleado), 'Ada Lovelace (DNI: 123)')

    def test_eliminar_empleado_desactiva_su_usuario(self):
        usuario = SimpleNamespace(is_active=True, save=Mock())
        empleado = SimpleNamespace(
            id_user=usuario,
            delete=Mock(),
        )

        with patch('empleados.api.view.transaction.atomic', nullcontext):
            EmpleadosViewSet().perform_destroy(empleado)

        self.assertFalse(usuario.is_active)
        usuario.save.assert_called_once_with(update_fields=['is_active'])
        empleado.delete.assert_called_once_with()

    def test_eliminar_empleado_sin_usuario_no_intenta_desactivar_cuenta(self):
        empleado = SimpleNamespace(id_user=None, delete=Mock())

        with patch('empleados.api.view.transaction.atomic', nullcontext):
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
        filtrar.assert_called_once_with(id_user__groups__name='Barberos')

    def test_ruta_de_roles_ya_no_esta_registrada(self):
        with self.assertRaises(Resolver404):
            resolve('/api/roles/')

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
