from django.utils import timezone
from rest_framework import serializers

from cajas.api.fields import UTCDateTimeField
from cajas.models import Cajas, MovimientosCajas


class CajasSerializer(serializers.ModelSerializer):
    fecha_inicio = UTCDateTimeField()
    fecha_cierre = UTCDateTimeField(allow_null=True)
    empleado_nombre = serializers.CharField(
        source='id_empleado.nombre', read_only=True
    )
    empleado_apellido = serializers.CharField(
        source='id_empleado.apellido', read_only=True
    )

    class Meta:
        model = Cajas
        fields = '__all__'


class MovimientosCajasSerializer(serializers.ModelSerializer):
    fecha = UTCDateTimeField(required=False)

    class Meta:
        model = MovimientosCajas
        fields = '__all__'

    def create(self, validated_data):
        validated_data.setdefault('fecha', timezone.now())
        return super().create(validated_data)


class AbrirCajaSerializer(serializers.Serializer):
    usuario = serializers.CharField(max_length=150)
    contrasena = serializers.CharField(
        trim_whitespace=False, write_only=True
    )
    saldo_inicial = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0
    )


class CerrarCajaSerializer(serializers.Serializer):
    usuario = serializers.CharField(max_length=150)
    contrasena = serializers.CharField(
        trim_whitespace=False, write_only=True
    )
    saldo_real = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0
    )
