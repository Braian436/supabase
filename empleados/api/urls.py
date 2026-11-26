from django.urls import path
from rest_framework.routers import DefaultRouter
from empleados.api.view import (
    AsistenciasDiaAPIView,
    BarberosPublicosAPIView,
    EmpleadosViewSet,
    GruposAPIView,
    LiquidacionesSemanalesViewSet,
    RegistrosAsistenciasViewSet,
)

router = DefaultRouter()
router.register('empleados', EmpleadosViewSet, basename='empleados')
router.register('asistencias', RegistrosAsistenciasViewSet, basename='asistencias')
router.register(
    'liquidaciones',
    LiquidacionesSemanalesViewSet,
    basename='liquidaciones',
)
urlpatterns = [
    path('barberos/', BarberosPublicosAPIView.as_view(), name='barberos-publicos'),
    path('grupos/', GruposAPIView.as_view(), name='grupos-list'),
    path(
        'asistencias/dia/',
        AsistenciasDiaAPIView.as_view(),
        name='asistencias-dia',
    ),
    *router.urls,
]
