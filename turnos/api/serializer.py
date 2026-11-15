from rest_framework import serializers


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
