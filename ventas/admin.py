from django.contrib import admin

from .models import DetallesProductos, DetallesServicios, Ventas

admin.site.register(Ventas)
admin.site.register(DetallesServicios)
admin.site.register(DetallesProductos)
