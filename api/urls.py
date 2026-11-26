from django.urls import path
from .views import DashboardAdministradorAPIView, EstadoAPIView

urlpatterns = [
    path(
        'dashboard/administrador/',
        DashboardAdministradorAPIView.as_view(),
        name='dashboard-administrador',
    ),
    path('estado/', EstadoAPIView.as_view(), name='api-estado'),
]
