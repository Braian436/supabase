from rest_framework import serializers

from turnos.models import Clientes, Turnos


class DisponibilidadQuerySerializer(serializers.Serializer):
    empleado = serializers.IntegerField(min_value=1)
    desde = serializers.DateField()
    hasta = serializers.DateField()
    horas = serializers.ListField(
        child=serializers.TimeField(format='%H:%M', input_formats=['%H:%M']),
        allow_empty=False,
        max_length=24,
    )

    def validate(self, attrs):
        if attrs['hasta'] < attrs['desde']:
            raise serializers.ValidationError(
                {'hasta': 'Debe ser igual o posterior a desde.'}
            )
        if (attrs['hasta'] - attrs['desde']).days > 30:
            raise serializers.ValidationError(
                {'hasta': 'El rango no puede superar 31 días.'}
            )
        if len(set(attrs['horas'])) != len(attrs['horas']):
            raise serializers.ValidationError(
                {'horas': 'No se permiten horarios repetidos.'}
            )
        return attrs


class ReservaTurnoSerializer(serializers.Serializer):
    empleado = serializers.IntegerField(min_value=1)
    fecha = serializers.DateField()
    hora = serializers.TimeField(format='%H:%M', input_formats=['%H:%M'])
    nombre = serializers.CharField(allow_blank=False, trim_whitespace=True)
    apellido = serializers.CharField(allow_blank=False, trim_whitespace=True)
    telefono = serializers.CharField(allow_blank=False, trim_whitespace=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True, default='')
    servicios = serializers.ListField(
        child=serializers.IntegerField(min_value=1), required=False, allow_empty=True, default=list
    )
    id_servicio = serializers.IntegerField(min_value=1, required=False)


class ClientesSerializer(serializers.ModelSerializer):
    fecha_nacimiento = serializers.DateField(required=False, allow_null=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Clientes
        fields = ('id_cliente', 'nombre', 'apellido', 'telefono', 'email', 'fecha_nacimiento')

    def _limpiar(self, value, etiqueta):
        texto = value.strip()
        if not texto:
            raise serializers.ValidationError(f'El {etiqueta} es obligatorio.')
        return texto

    def validate_nombre(self, value):
        return self._limpiar(value, 'nombre')

    def validate_apellido(self, value):
        return self._limpiar(value, 'apellido')

    def validate_telefono(self, value):
        return self._limpiar(value, 'teléfono')

    def validate_email(self, value):
        email = (value or '').strip()
        return email or None


class TurnosSerializer(serializers.ModelSerializer):
    cliente = serializers.SerializerMethodField()
    barbero = serializers.SerializerMethodField()
    servicios = serializers.SerializerMethodField()
    hora = serializers.TimeField(format='%H:%M', read_only=True)

    class Meta:
        model = Turnos
        fields = (
            'id_turno',
            'fecha',
            'hora',
            'estado',
            'cliente',
            'barbero',
            'servicios',
        )

    def get_cliente(self, turno):
        cliente = turno.id_cliente
        if cliente is None:
            return None
        return {
            'id_cliente': cliente.pk,
            'nombre': cliente.nombre,
            'apellido': cliente.apellido,
            'telefono': cliente.telefono,
            'email': cliente.email,
        }

    def get_barbero(self, turno):
        empleado = turno.id_empleado
        if empleado is None:
            return None
        return {
            'id_empleado': empleado.pk,
            'nombre': empleado.nombre,
            'apellido': empleado.apellido,
        }

    def get_servicios(self, turno):
        return [
            {
                'id_servicio': servicio.id_servicio.pk,
                'nombre': servicio.id_servicio.nombre,
                'precio': str(servicio.id_servicio.precio),
            }
            for servicio in turno.servicios_turnos.all()
            if servicio.id_servicio_id
        ]
