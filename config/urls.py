"""
URL configuration for config project.
"""
from django.urls import path, include

from core.views import home

urlpatterns = [
    path('', home, name='home'),

    
    # Todas las rutas de la API REST quedan agrupadas bajo el prefijo /api/.
    # A medida que agreguen mas endpoints (por app), inclúyanlos aca mismo,
    # por ejemplo: path('api/turnos/', include('turnos.api.urls')).
    path('api/', include('api.urls')),

    path('api/', include('empleados.api.urls')),
    path('api/', include('turnos.api.urls')),

]
