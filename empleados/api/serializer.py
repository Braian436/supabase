from rest_framework import serializers
from empleados.models import Empleados

class EmpleadosSerializaer(serializers.ModelSerializer):
    class Meta:
        model= Empleados
        fields= '__all__'