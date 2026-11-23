from rest_framework import serializers

from servicios.models import Servicios


class ServiciosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicios
        fields = ('id_servicio', 'nombre', 'descripcion', 'precio')
