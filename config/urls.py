"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include

from core.views import home

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),

    # Todas las rutas de la API REST quedan agrupadas bajo el prefijo /api/.
    # A medida que agreguen mas endpoints (por app), inclúyanlos aca mismo,
    # por ejemplo: path('api/turnos/', include('turnos.api.urls')).
    path('api/', include('api.urls')),

    path('api/', include('productos.api.urls')),
    path('api/', include('compras.api.urls')),
    path('api/', include('servicios.api.urls')),
    path('api/', include('empleados.api.urls')),
    path('api/', include('turnos.api.urls')),
    path('api/', include('cajas.api.urls')),
    path('api/', include('ventas.api.urls')),

]
