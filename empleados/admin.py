from django.contrib import admin

from .models import (
    Empleados,
    LiquidacionesSemanales,
    RegistrosAsistencias,
    Roles,
)

admin.site.register(Empleados)
admin.site.register(RegistrosAsistencias)
admin.site.register(LiquidacionesSemanales)
admin.site.register(Roles)
