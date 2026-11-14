from django.urls import path

from turnos.api.view import (
    DisponibilidadTurnosAPIView,
    ReservarTurnoAPIView,
)


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
]
