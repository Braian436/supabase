from django.urls import path

from api.auth import LoginAPIView, LogoutAPIView, MeAPIView
from api.views import (
    DashboardAdministradorAPIView,
    DashboardBarberoAPIView,
    EstadoAPIView,
)

urlpatterns = [
    path(
        'dashboard/administrador/',
        DashboardAdministradorAPIView.as_view(),
        name='dashboard-administrador',
    ),
    path(
        'dashboard/barbero/',
        DashboardBarberoAPIView.as_view(),
        name='dashboard-barbero',
    ),
    path('auth/login/', LoginAPIView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutAPIView.as_view(), name='auth-logout'),
    path('auth/me/', MeAPIView.as_view(), name='auth-me'),
    path('estado/', EstadoAPIView.as_view(), name='api-estado'),
]
