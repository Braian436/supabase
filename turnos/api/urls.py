from django.urls import path
from rest_framework.routers import DefaultRouter

from turnos.api.view import (
    ClientesViewSet,
    DisponibilidadTurnosAPIView,
    ReservarTurnoAPIView,
)

router = DefaultRouter()
router.register('clientes', ClientesViewSet, basename='clientes')

urlpatterns = [
    path(
        'turnos/disponibilidad/',
        DisponibilidadTurnosAPIView.as_view(),
        name='turnos-disponibilidad',
    ),
    path(
        'turnos/reservas/',
        ReservarTurnoAPIView.as_view(),
        name='turnos-reserva',
    ),
    *router.urls,
]
