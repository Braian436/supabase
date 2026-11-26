from django.contrib import admin

from .models import DetallesProductos, DetallesServicios, Ventas


@admin.register(Ventas)
class VentasAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(DetallesServicios)
admin.site.register(DetallesProductos)
