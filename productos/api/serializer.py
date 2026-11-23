from rest_framework import serializers

from productos.models import Categorias, Descuentos, Marcas, Productos


class ProductosSerializer(serializers.ModelSerializer):
    marca_nombre = serializers.CharField(source='id_marca.nombre', read_only=True)
    categoria_nombre = serializers.CharField(source='id_categoria.nombre', read_only=True)
    descuento_nombre = serializers.CharField(source='id_descuento.nombre', read_only=True)

    class Meta:
        model = Productos
        fields = (
            'id_producto',
            'nombre',
            'descripcion',
            'stock_actual',
            'stock_minimo',
            'estado',
            'id_marca',
            'marca_nombre',
            'id_categoria',
            'categoria_nombre',
            'id_descuento',
            'descuento_nombre',
        )


class MarcasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marcas
        fields = ('id_marca', 'nombre')


class CategoriasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorias
        fields = ('id_categoria', 'nombre', 'descripcion', 'estado')


class DescuentosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Descuentos
        fields = ('id_descuento', 'nombre', 'mayorista', 'cantidad')


class PreciosProductosSerializer(serializers.Serializer):
    id_producto = serializers.IntegerField(read_only=True)
    costo_ultima_compra = serializers.DecimalField(
        max_digits=12, decimal_places=2, allow_null=True, read_only=True,
    )
    precio_ultima_venta = serializers.DecimalField(
        max_digits=12, decimal_places=2, allow_null=True, read_only=True,
    )
