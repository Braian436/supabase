from django.contrib import admin

from .models import Turnos, ServiciosTurnos, Servicios, HistorialesTurnos

admin.site.register(Turnos)
admin.site.register(ServiciosTurnos)
admin.site.register(Servicios)
admin.site.register(HistorialesTurnos)