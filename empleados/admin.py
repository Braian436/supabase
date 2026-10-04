from django.contrib import admin

from .models import Empleados, RegistrosDeAsistencias, Liquidaciones, Roles, Alquileres, Apertura, PagosAlquileres

admin.site.register(Empleados)
admin.site.register(RegistrosDeAsistencias)
admin.site.register(Liquidaciones)
admin.site.register(Roles)
admin.site.register(Alquileres)
admin.site.register(Apertura)
admin.site.register(PagosAlquileres)