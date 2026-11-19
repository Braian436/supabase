from rest_framework import serializers
from empleados.models import Empleados, LiquidacionesSemanales


class EmpleadosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleados
        fields = '__all__'


class BarberoPublicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleados
        fields = ('id_empleado', 'nombre', 'apellido', 'foto_empleado')


class LiquidacionesSemanalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiquidacionesSemanales
        fields = '__all__'