from django.contrib import admin

from .models import Empleados, RegistrosDeAsistencias, Liquidaciones, Roles

admin.site.register(Empleados)
admin.site.register(RegistrosDeAsistencias)
admin.site.register(Liquidaciones)
admin.site.register(Roles)