from django.contrib import admin

from .models import Ordenes, PagosOrdenes, DetallesServicios, DetallesProductos

admin.site.register(Ordenes)
admin.site.register(PagosOrdenes)
admin.site.register(DetallesServicios)
admin.site.register(DetallesProductos)