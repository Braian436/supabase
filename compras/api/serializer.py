from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from compras.models import Compras, DetallesCompras
from productos.models import Productos


class DetalleCompraSerializer(serializers.ModelSerializer):
    id_producto = serializers.IntegerField(source='id_producto_id', read_only=True)
    producto_nombre = serializers.CharField(source='id_producto.nombre', read_only=True)

    class Meta:
        model = DetallesCompras
        fields = (
            'id_detalle_compra',
            'id_producto',
            'producto_nombre',
            'cantidad',
            'precio_unitario',
            'importe',
            'subtotal',
        )


class CompraSerializer(serializers.ModelSerializer):
    detalles = DetalleCompraSerializer(source='detallescompras_set', many=True, read_only=True)

    class Meta:
        model = Compras
        fields = ('id_compra', 'fecha', 'total', 'detalles')


class DetalleCompraCreateSerializer(serializers.Serializer):
    id_producto = serializers.IntegerField(min_value=1)
    cantidad = serializers.IntegerField(min_value=1)
    precio_unitario = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0'),
    )


class CompraCreateSerializer(serializers.Serializer):
    detalles = DetalleCompraCreateSerializer(many=True, allow_empty=False)

    def validate_detalles(self, detalles):
        ids = [detalle['id_producto'] for detalle in detalles]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError('No repitas un producto en la compra.')
        return detalles

    def create(self, validated_data):
        detalles = validated_data['detalles']
        ids = [detalle['id_producto'] for detalle in detalles]

        with transaction.atomic():
            productos = Productos.objects.select_for_update().in_bulk(ids)
            if len(productos) != len(ids):
                raise serializers.ValidationError('Uno o más productos no existen.')

            importes = [
                (detalle, detalle['precio_unitario'] * detalle['cantidad'])
                for detalle in detalles
            ]
            compra = Compras.objects.create(
                fecha=timezone.now(),
                total=sum((importe for _, importe in importes), Decimal('0')),
            )

            for detalle, importe in importes:
                producto = productos[detalle['id_producto']]
                DetallesCompras.objects.create(
                    id_compra=compra,
                    id_producto=producto,
                    cantidad=detalle['cantidad'],
                    precio_unitario=detalle['precio_unitario'],
                    importe=importe,
                    subtotal=importe,
                )
                producto.stock_actual += detalle['cantidad']
                producto.save(update_fields=['stock_actual'])

        return compra
