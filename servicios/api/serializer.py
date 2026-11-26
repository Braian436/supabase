from rest_framework import serializers

from servicios.models import EmpleadosServicios, Servicios


class ServiciosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicios
        fields = ('id_servicio', 'nombre', 'descripcion', 'precio')

    def validate_nombre(self, value):
        nombre = value.strip()
        if not nombre:
            raise serializers.ValidationError('El nombre del servicio es obligatorio.')
        return nombre

    def validate_precio(self, value):
        if value < 0:
            raise serializers.ValidationError('El precio no puede ser negativo.')
        return value


class EmpleadosServiciosSerializer(serializers.ModelSerializer):
    descripcion = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')

    class Meta:
        model = EmpleadosServicios
        fields = ('id_empleado_servicio', 'id_empleado', 'id_servicio', 'descripcion')

    def validate(self, attrs):
        empleado = attrs.get('id_empleado', getattr(self.instance, 'id_empleado', None))
        servicio = attrs.get('id_servicio', getattr(self.instance, 'id_servicio', None))
        qs = EmpleadosServicios.objects.filter(id_empleado=empleado, id_servicio=servicio)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Ese barbero ya está asignado a este servicio.')
        return attrs
