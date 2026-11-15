from django.contrib import admin

from .models import Clientes, Turnos, TurnosExpress

admin.site.register(Clientes)
admin.site.register(Turnos)
admin.site.register(TurnosExpress)
