from django.db import models

class Productos(models.Model):
    id_producto = models.AutoField(primary_key=True)
    id_marca = models.ForeignKey('productos.Marcas', models.DO_NOTHING, db_column='id_marca')
    id_descuento = models.ForeignKey('productos.Descuentos', models.DO_NOTHING, db_column='id_descuento', blank=True, null=True)
    codigo_barra = models.BigIntegerField(blank=True, null=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255)
    tipo = models.CharField(max_length=50, blank=True, null=True)
    estado = models.BooleanField(blank=True, null=True)
    costo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'productos'

    def __str__(self):
        nombre_prod = self.nombre or "Producto sin nombre"
        marca = self.id_marca if self.id_marca else "Sin marca"
        codigo = self.codigo_barra or "Sin código"
        return f"{nombre_prod} (Cód: {codigo}) | {marca}"

class Descuentos(models.Model):
    id_descuento = models.AutoField(primary_key=True)
    nombre = models.TextField()
    mayorista = models.BooleanField()
    cantidad = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'descuentos'

    def __str__(self):
        return f"Descuento: {self.nombre}"

class Stock(models.Model):
    id_stock = models.AutoField(primary_key=True)
    id_producto = models.ForeignKey('productos.Productos', models.DO_NOTHING, db_column='id_producto')
    cantidad_actual = models.IntegerField()
    stock_minimo = models.IntegerField()
    ultima_actualizacion = models.DateTimeField(blank=True, null=True)
    tipo_movimiento = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stock'

    def __str__(self):
        return f"Stock: {self.id_producto} - {self.cantidad_actual}"

class Marcas(models.Model):
    id_marca = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey('productos.Categorias', models.DO_NOTHING, db_column='id_categoria')
    nombre = models.CharField(max_length=80)

    class Meta:
        managed = False
        db_table = 'marcas'

    def __str__(self):
        return f"Marca: {self.nombre}"

class Categorias(models.Model):
    id_categoria = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=80)
    descripcion = models.CharField(max_length=80, blank=True, null=True)
    estado = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'categorias'

    def __str__(self):
        return f"Categoría: {self.nombre}"
