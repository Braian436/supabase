from django.contrib import admin

from .models import Productos, Descuentos, Marcas, Categorias

admin.site.register(Productos)
admin.site.register(Descuentos)
admin.site.register(Marcas)
admin.site.register(Categorias)