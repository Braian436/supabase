from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AbrirCajaAPIView,
    CajasViewSet,
    CerrarCajaAPIView,
    MovimientosCajasViewSet,
)

router = DefaultRouter()
router.register('cajas', CajasViewSet, basename='cajas')
router.register('movimientos-cajas', MovimientosCajasViewSet, basename='movimientos-cajas')

urlpatterns = [
    path('cajas/abrir/', AbrirCajaAPIView.as_view(), name='cajas-abrir'),
    path('cajas/<int:pk>/cerrar/', CerrarCajaAPIView.as_view(), name='cajas-cerrar'),
    *router.urls,
]
