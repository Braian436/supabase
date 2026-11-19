"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include

from core.views import home
from api.views import AuthMeAPIView, LogoutAPIView, TokenLoginAPIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),

    
    # Todas las rutas de la API REST quedan agrupadas bajo el prefijo /api/.
    # A medida que agreguen mas endpoints (por app), inclúyanlos aca mismo,
    # por ejemplo: path('api/turnos/', include('turnos.api.urls')).
    path('api/', include('api.urls')),

    path('api/', include('empleados.api.urls')),
    path('api/', include('turnos.api.urls')),

    path('api/auth/token/', TokenLoginAPIView.as_view(), name='api-token-auth'),
    path('api/auth/me/', AuthMeAPIView.as_view(), name='api-auth-me'),
    path('api/auth/logout/', LogoutAPIView.as_view(), name='api-auth-logout'),
]
