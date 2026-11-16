from django.db import models


class Productos(models.Model):
    id_producto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    stock_actual = models.IntegerField()
    stock_minimo = models.IntegerField(blank=True, null=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    estado = models.BooleanField()
    id_marca = models.ForeignKey('Marcas', models.DO_NOTHING, db_column='id_marca')
    id_categoria = models.ForeignKey('Categorias', models.DO_NOTHING, db_column='id_categoria')
    id_descuento = models.ForeignKey('Descuentos', models.DO_NOTHING, db_column='id_descuento')

    class Meta:
        managed = False
        db_table = 'productos'

    def __str__(self):
        return f"{self.nombre} | Marca: {self.id_marca} | Stock: {self.stock_actual}"


class Marcas(models.Model):
    id_marca = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=80)

    class Meta:
        managed = False
        db_table = 'marcas'

    def __str__(self):
        return f"Marca: {self.nombre}"


class Categorias(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=80)
    descripcion = models.CharField(max_length=80, blank=True, null=True)
    estado = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'categorias'

    def __str__(self):
        return f"Categoría: {self.nombre}"


class Descuentos(models.Model):
    id_descuento = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=80)
    mayorista = models.BooleanField()
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'descuentos'

    def __str__(self):
        return f"Descuento: {self.nombre}"
