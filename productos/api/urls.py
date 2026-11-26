from django.urls import include, path
from rest_framework.routers import DefaultRouter

from productos.api.view import (
    CategoriasViewSet,
    DescuentosViewSet,
    MarcasViewSet,
    PreciosProductosAPIView,
    ProductosViewSet,
)

router = DefaultRouter()
router.register('productos', ProductosViewSet, basename='productos')
router.register('marcas', MarcasViewSet, basename='marcas')
router.register('categorias', CategoriasViewSet, basename='categorias')
router.register('descuentos', DescuentosViewSet, basename='descuentos')

urlpatterns = [
    path('productos/precios/', PreciosProductosAPIView.as_view(), name='productos-precios'),
    path('', include(router.urls)),
]
