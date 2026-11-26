from django.db import IntegrityError
from django.db.models import OuterRef, Subquery
from rest_framework import generics, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny

from compras.models import DetallesCompras
from productos.api.serializer import (
    CategoriasSerializer,
    DescuentosSerializer,
    MarcasSerializer,
    PreciosProductosSerializer,
    ProductosSerializer,
)
from productos.models import Categorias, Descuentos, Marcas, Productos
from ventas.models import DetallesProductos


class CatalogoSeguroMixin:
    def perform_destroy(self, instance):
        try:
            instance.delete()
        except IntegrityError as exc:
            raise ValidationError('No se puede eliminar porque está en uso por un producto.') from exc


class ProductosViewSet(viewsets.ModelViewSet):
    queryset = (
        Productos.objects.select_related('id_marca', 'id_categoria', 'id_descuento')
        .order_by('id_producto')
    )
    serializer_class = ProductosSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class MarcasViewSet(CatalogoSeguroMixin, viewsets.ModelViewSet):
    queryset = Marcas.objects.all().order_by('nombre')
    serializer_class = MarcasSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class CategoriasViewSet(CatalogoSeguroMixin, viewsets.ModelViewSet):
    queryset = Categorias.objects.all().order_by('nombre')
    serializer_class = CategoriasSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class DescuentosViewSet(CatalogoSeguroMixin, viewsets.ModelViewSet):
    queryset = Descuentos.objects.all().order_by('nombre')
    serializer_class = DescuentosSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class PreciosProductosAPIView(generics.ListAPIView):
    serializer_class = PreciosProductosSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        ultima_compra = (
            DetallesCompras.objects.filter(id_producto=OuterRef('pk'))
            .order_by('-id_compra__fecha', '-id_detalle_compra')
            .values('precio_unitario')[:1]
        )
        ultima_venta = (
            DetallesProductos.objects.filter(id_producto=OuterRef('pk'))
            .order_by('-id_venta__fecha_venta', '-id_detalle_producto')
            .values('precio_unitario')[:1]
        )
        return Productos.objects.order_by('id_producto').annotate(
            costo_ultima_compra=Subquery(ultima_compra),
            precio_ultima_venta=Subquery(ultima_venta),
        ).values('id_producto', 'costo_ultima_compra', 'precio_ultima_venta')
