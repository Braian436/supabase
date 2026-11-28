from rest_framework import serializers

from cajas.api.fields import UTCDateTimeField
from ventas.models import DetallesProductos, DetallesServicios, Ventas


class DetalleProductoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(
        source='id_producto.nombre', read_only=True
    )

    class Meta:
        model = DetallesProductos
        fields = (
            'id_detalle_producto',
            'id_producto',
            'producto_nombre',
            'precio_unitario',
            'cantidad',
            'importe',
        )


class DetalleServicioSerializer(serializers.ModelSerializer):
    servicio_nombre = serializers.CharField(
        source='id_servicio.nombre', read_only=True
    )

    class Meta:
        model = DetallesServicios
        fields = (
            'id_detalle_servicio',
            'id_servicio',
            'servicio_nombre',
            'precio_unitario',
            'cantidad',
            'importe',
        )


class VentaSerializer(serializers.ModelSerializer):
    fecha_venta = UTCDateTimeField()
    fecha_cierre = UTCDateTimeField(allow_null=True)
    detalles_productos = DetalleProductoSerializer(
        source='detallesproductos_set', many=True, read_only=True
    )
    detalles_servicios = DetalleServicioSerializer(
        source='detallesservicios_set', many=True, read_only=True
    )
    cliente_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Ventas
        fields = '__all__'

    def get_cliente_nombre(self, obj):
        cliente = obj.id_cliente
        if not cliente:
            return ''
        nombre = getattr(cliente, 'nombre', '')
        apellido = getattr(cliente, 'apellido', '')
        return f"{nombre} {apellido}".strip()


class CobrarVentaSerializer(serializers.Serializer):
    metodo_pago = serializers.ChoiceField(
        choices=['efectivo', 'tarjeta', 'transferencia']
    )
    monto_recibido = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True,
        default=None,
    )


class AgregarItemVentaSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=['servicio', 'producto'])
    id_item = serializers.IntegerField(min_value=1)
    cantidad = serializers.IntegerField(min_value=1, default=1)


class ItemServicioSerializer(serializers.Serializer):
    id_servicio = serializers.IntegerField(min_value=1)
    cantidad = serializers.IntegerField(min_value=1)


class ItemProductoSerializer(serializers.Serializer):
    id_producto = serializers.IntegerField(min_value=1)
    cantidad = serializers.IntegerField(min_value=1)


class ClienteNuevoSerializer(serializers.Serializer):
    telefono = serializers.CharField(max_length=18, trim_whitespace=True)
    nombre = serializers.CharField(max_length=80, trim_whitespace=True)
    apellido = serializers.CharField(max_length=50, trim_whitespace=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True, default='')


class CrearTicketSerializer(serializers.Serializer):
    id_cliente = serializers.IntegerField(required=False, allow_null=True)
    cliente = ClienteNuevoSerializer(required=False)
    servicios = ItemServicioSerializer(many=True, required=False, default=list)
    productos = ItemProductoSerializer(many=True, required=False, default=list)
    descuento = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, default=0
    )

    def validate(self, attrs):
        if not attrs.get('servicios') and not attrs.get('productos'):
            raise serializers.ValidationError({
                'detalle': 'Agregá al menos un servicio o producto.'
            })
        if not attrs.get('id_cliente') and not attrs.get('cliente'):
            raise serializers.ValidationError({
                'cliente': 'Indicá un cliente existente o uno nuevo.'
            })
        return attrs


class AnularVentaSerializer(serializers.Serializer):
    motivo = serializers.CharField(
        max_length=200,
        min_length=5,
        trim_whitespace=True,
    )
    usuario = serializers.CharField(max_length=150, trim_whitespace=True)
    contrasena = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )


class CancelarVentaSerializer(serializers.Serializer):
    motivo = serializers.CharField(
        max_length=200,
        min_length=5,
        trim_whitespace=True,
    )

