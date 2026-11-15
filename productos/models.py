from django.db import models

class Productos(models.Model):
    id_producto = models.AutoField(primary_key=True)
    nombre = models.CharField()
    stock_actual = models.IntegerField()
    stock_minimo = models.IntegerField(blank=True, null=True)
    descripcion = models.CharField(blank=True, null=True)
    estado = models.BooleanField()
    id_marca = models.ForeignKey('Marcas', models.DO_NOTHING, db_column='id_marca')
    id_categoria = models.ForeignKey('Categorias', models.DO_NOTHING, db_column='id_categoria')
    id_descuento = models.ForeignKey('Descuentos', models.DO_NOTHING, db_column='id_descuento')

    class Meta:
        managed = False
        db_table = 'productos'

    # def __str__(self):
    #     nombre_prod = self.nombre or "Producto sin nombre"
    #     marca = self.id_marca if self.id_marca else "Sin marca"
    #     codigo = self.codigo_barra or "Sin código"
    #     return f"{nombre_prod} (Cód: {codigo}) | {marca}"

class Descuentos(models.Model):
    id_descuento = models.AutoField(primary_key=True)
    nombre = models.CharField()
    mayorista = models.BooleanField()
    cantidad = models.DecimalField(max_digits=65535, decimal_places=65535)

    class Meta:
        managed = False
        db_table = 'descuentos'

    # def __str__(self):
    #     return f"Descuento: {self.nombre}"

class Marcas(models.Model):
    id_marca = models.AutoField(primary_key=True)
    nombre = models.CharField()

    class Meta:
        managed = False
        db_table = 'marcas'

    # def __str__(self):
    #     return f"Marca: {self.nombre}"

class Categorias(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField()
    descripcion = models.CharField(blank=True, null=True)
    estado = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'categorias'

    # def __str__(self):
    #     return f"Categoría: {self.nombre}"
