from django.contrib import admin

from .models import EmpleadosServicios, Servicios, ServiciosTurnos

admin.site.register(Servicios)
admin.site.register(ServiciosTurnos)
admin.site.register(EmpleadosServicios)
