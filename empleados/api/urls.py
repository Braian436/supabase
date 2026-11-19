from django.urls import path
from rest_framework.routers import DefaultRouter
from empleados.api.view import (
    BarberosPublicosAPIView,
    EmpleadosViewSet,
    LiquidacionesSemanalesViewSet,
)

router = DefaultRouter()
router.register('empleados', EmpleadosViewSet, basename='empleados')
router.register(
    'liquidaciones',
    LiquidacionesSemanalesViewSet,
    basename='liquidaciones',
)
urlpatterns = [
    path('barberos/', BarberosPublicosAPIView.as_view(), name='barberos-publicos'),
    *router.urls,
]
