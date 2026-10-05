from django.contrib import admin

from .models import Turnos, ServiciosTurnos, Servicios

admin.site.register(Turnos)
admin.site.register(ServiciosTurnos)
admin.site.register(Servicios)