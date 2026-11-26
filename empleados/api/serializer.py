from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from empleados.models import Empleados, LiquidacionesSemanales, RegistrosAsistencias


class EmpleadosSerializer(serializers.ModelSerializer):
    cuenta = serializers.SerializerMethodField()
    rol_laboral = serializers.SerializerMethodField()
    usuario = serializers.CharField(required=False, allow_blank=True, max_length=150, write_only=True)
    contrasena = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=128,
        trim_whitespace=False,
        write_only=True,
    )
    grupo_usuario = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Empleados
        fields = (
            'id_empleado',
            'rol_laboral',
            'nombre',
            'apellido',
            'dni',
            'foto_empleado',
            'porcentaje_comision',
            'cuenta',
            'usuario',
            'contrasena',
            'grupo_usuario',
        )

    def _obtener_cuenta(self, empleado):
        """Devuelve el usuario de auth vinculado al empleado, si existe."""
        if empleado is None:
            return None
        return empleado.id_user

    def get_rol_laboral(self, empleado):
        usuario = self._obtener_cuenta(empleado)
        if usuario is None:
            return ''
        grupo = usuario.groups.first()
        return grupo.name if grupo else ''

    def get_cuenta(self, empleado):
        usuario = self._obtener_cuenta(empleado)
        if usuario is None:
            return None
        grupo = next(iter(usuario.groups.all()), None)
        return {
            'usuario': usuario.get_username(),
            'grupo': grupo.name if grupo else '',
        }

    def validate(self, attrs):
        cuenta_existente = self._obtener_cuenta(self.instance)
        campos_cuenta = ('usuario', 'contrasena', 'grupo_usuario')
        valores = {campo: attrs.get(campo, '') for campo in campos_cuenta}
        completos = all(valores.values())
        alguno_informado = any(valores.values())

        if cuenta_existente is None and alguno_informado and not completos:
            raise serializers.ValidationError(
                'Para crear una cuenta completá usuario, contraseña y grupo.'
            )

        if not alguno_informado:
            return attrs

        usuario_actual = cuenta_existente
        username = valores['usuario']
        if username:
            usuarios = get_user_model().objects.filter(username=username)
            if usuario_actual:
                usuarios = usuarios.exclude(pk=usuario_actual.pk)
            if usuarios.exists():
                raise serializers.ValidationError({
                    'usuario': 'Ese nombre de usuario ya está en uso.',
                })

        nombre_grupo = valores['grupo_usuario']
        if nombre_grupo and not Group.objects.filter(name=nombre_grupo).exists():
            raise serializers.ValidationError({
                'grupo_usuario': 'Seleccioná un grupo existente.',
            })

        contrasena = valores['contrasena']
        if contrasena:
            try:
                validate_password(contrasena, user=usuario_actual)
            except DjangoValidationError as error:
                raise serializers.ValidationError({
                    'contrasena': error.messages,
                }) from error

        return attrs

    def _guardar_cuenta(self, empleado, datos):
        usuario = datos.get('usuario', '')
        contrasena = datos.get('contrasena', '')
        nombre_grupo = datos.get('grupo_usuario', '')
        if not any((usuario, contrasena, nombre_grupo)):
            return

        usuario_actual = self._obtener_cuenta(empleado)
        if usuario_actual is None:
            User = get_user_model()
            usuario_nuevo = User.objects.create_user(
                username=usuario,
                password=contrasena,
            )
            empleado.id_user = usuario_nuevo
            empleado.save(update_fields=['id_user'])
        else:
            usuario_nuevo = usuario_actual
            campos_actualizados = []
            if usuario:
                usuario_actual.username = usuario
                campos_actualizados.append('username')
            if contrasena:
                usuario_actual.set_password(contrasena)
                campos_actualizados.append('password')
            if campos_actualizados:
                usuario_actual.save(update_fields=campos_actualizados)

        if nombre_grupo:
            grupo = Group.objects.get(name=nombre_grupo)
            usuario_nuevo.groups.set([grupo])

    def create(self, validated_data):
        datos_cuenta = {
            campo: validated_data.pop(campo, '')
            for campo in ('usuario', 'contrasena', 'grupo_usuario')
        }
        with transaction.atomic():
            empleado = super().create(validated_data)
            self._guardar_cuenta(empleado, datos_cuenta)
        return empleado

    def update(self, instance, validated_data):
        datos_cuenta = {
            campo: validated_data.pop(campo, '')
            for campo in ('usuario', 'contrasena', 'grupo_usuario')
        }
        with transaction.atomic():
            empleado = super().update(instance, validated_data)
            self._guardar_cuenta(empleado, datos_cuenta)
        return empleado


class BarberoPublicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleados
        fields = ('id_empleado', 'nombre', 'apellido', 'foto_empleado')


ESTADOS_ASISTENCIA = ('presente', 'ausente', 'justificado')


class RegistrosAsistenciasSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(
        source='id_empleado.nombre',
        read_only=True,
    )
    empleado_apellido = serializers.CharField(
        source='id_empleado.apellido',
        read_only=True,
    )
    rol = serializers.SerializerMethodField()
    hora_entrada = serializers.TimeField(required=False, allow_null=True)
    hora_salida = serializers.TimeField(required=False, allow_null=True)
    estado = serializers.ChoiceField(
        choices=ESTADOS_ASISTENCIA,
        required=False,
        default='presente',
    )
    observacion = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        max_length=200,
    )

    class Meta:
        model = RegistrosAsistencias
        fields = (
            'id_asistencias',
            'id_empleado',
            'empleado_nombre',
            'empleado_apellido',
            'rol',
            'fecha',
            'hora_entrada',
            'hora_salida',
            'fecha_modificacion',
            'estado',
            'observacion',
        )
        read_only_fields = ('fecha', 'fecha_modificacion')

    def get_rol(self, registro):
        usuario = getattr(registro.id_empleado, 'id_user', None)
        if usuario is None:
            return ''
        grupo = usuario.groups.first()
        return grupo.name if grupo else ''


class GrupoUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name')


class LiquidacionesSemanalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiquidacionesSemanales
        fields = '__all__'
