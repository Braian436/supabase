from django.contrib import admin

from .models import Productos, Descuentos, Stock, Marcas, Categorias

admin.site.register(Productos)
admin.site.register(Descuentos)
admin.site.register(Stock)
admin.site.register(Marcas)
admin.site.register(Categorias)