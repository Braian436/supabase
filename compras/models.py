from django.db import models


class Compras(models.Model):
    id_compra = models.AutoField(primary_key=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'compras'

    def __str__(self):
        return f"Compra {self.id_compra} - Fecha: {self.fecha} - Total: {self.total}"


class DetallesCompras(models.Model):
    id_detalle_compra = models.AutoField(primary_key=True)
    id_compra = models.ForeignKey(Compras, models.DO_NOTHING, db_column='id_compra')
    id_producto = models.ForeignKey('productos.Productos', models.DO_NOTHING, db_column='id_producto')
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    importe = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'detalles_compras'

    def __str__(self):
        return f"Detalle Compra {self.id_detalle_compra} - Compra: {self.id_compra} - Producto: {self.id_producto} - Cantidad: {self.cantidad} - Importe: {self.importe}"
