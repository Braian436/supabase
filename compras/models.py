from django.db import models

class Compras(models.Model):
    id_compra = models.AutoField(primary_key=True)
    nro_ticket = models.IntegerField(unique=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField()

    class Meta:
        managed = False
        db_table = 'compras'

    def __str__(self):
        return f"Compra {self.id_compra} - Ticket: {self.nro_ticket} - Total: {self.total}"

class DetallesCompras(models.Model):
    id_detalle_compra = models.AutoField(primary_key=True)
    id_compra = models.ForeignKey('compras.Compras', models.DO_NOTHING, db_column='id_compra')
    id_producto = models.ForeignKey('productos.Productos', models.DO_NOTHING, db_column='id_producto')
    descuento = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'detalles_compras'

    def __str__(self):
        return f"Detalle Compra {self.id_detalle_compra} - Compra: {self.id_compra} - Producto: {self.id_producto} - Descuento: {self.descuento} - Total: {self.total}"
