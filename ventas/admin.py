from django.contrib import admin

from .models import Ordenes, PagosOrden, DetalleServicios, DetalleProductos

admin.site.register(Ordenes)
admin.site.register(PagosOrden)
admin.site.register(DetalleServicios)
admin.site.register(DetalleProductos)