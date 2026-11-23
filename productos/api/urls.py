from django.urls import include, path
from rest_framework.routers import DefaultRouter

from productos.api.view import (
    CategoriasAPIView,
    DescuentosAPIView,
    MarcasAPIView,
    PreciosProductosAPIView,
    ProductosViewSet,
)

router = DefaultRouter()
router.register('productos', ProductosViewSet, basename='productos')

urlpatterns = [
    path('productos/precios/', PreciosProductosAPIView.as_view(), name='productos-precios'),
    path('marcas/', MarcasAPIView.as_view(), name='marcas-list'),
    path('categorias/', CategoriasAPIView.as_view(), name='categorias-list'),
    path('descuentos/', DescuentosAPIView.as_view(), name='descuentos-list'),
    path('', include(router.urls)),
]
