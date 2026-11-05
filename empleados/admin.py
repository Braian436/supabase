from django.contrib import admin

from .models import Empleados, RegistrosAsistencias, Liquidaciones, Roles, Alquileres, Aperturas, PagosAlquileres

admin.site.register(Empleados)
admin.site.register(RegistrosAsistencias)
admin.site.register(Liquidaciones)
admin.site.register(Roles)
admin.site.register(Alquileres)
admin.site.register(Aperturas)
admin.site.register(PagosAlquileres)