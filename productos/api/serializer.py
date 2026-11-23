from rest_framework import serializers

from productos.models import Categorias, Descuentos, Marcas, Productos


class ProductosSerializer(serializers.ModelSerializer):
    marca_nombre = serializers.CharField(source='id_marca.nombre', read_only=True)
    categoria_nombre = serializers.CharField(source='id_categoria.nombre', read_only=True)
    categoria_descripcion = serializers.CharField(
        source='id_categoria.descripcion', read_only=True, allow_null=True,
    )
    descuento_nombre = serializers.CharField(source='id_descuento.nombre', read_only=True)
    descuento_mayorista = serializers.BooleanField(
        source='id_descuento.mayorista', read_only=True, allow_null=True,
    )
    descuento_cantidad = serializers.DecimalField(
        source='id_descuento.cantidad',
        max_digits=10,
        decimal_places=2,
        read_only=True,
        allow_null=True,
    )

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
            'categoria_descripcion',
            'id_descuento',
            'descuento_nombre',
            'descuento_mayorista',
            'descuento_cantidad',
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
