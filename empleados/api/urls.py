from django.urls import path
from rest_framework.routers import DefaultRouter
from empleados.api.view import (
    BarberosPublicosAPIView,
    EmpleadosViewSet,
    GruposAPIView,
    LiquidacionesSemanalesViewSet,
    RolesAPIView,
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
    path('roles/', RolesAPIView.as_view(), name='roles-list'),
    path('grupos/', GruposAPIView.as_view(), name='grupos-list'),
    *router.urls,
]
