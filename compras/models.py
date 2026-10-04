from django.db import models

class Compras(models.Model):
    id_compra = models.AutoField(primary_key=True)
    nro_ticket = models.IntegerField(unique=True, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fecha = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'compras'

    def __str__(self):
        return f"Compra {self.id_compra} - Ticket: {self.nro_ticket} - Total: {self.total}"

class DetallesCompras(models.Model):
    id_detalle_compra = models.AutoField(primary_key=True)
    id_compra = models.ForeignKey('Compras', models.DO_NOTHING, db_column='id_compra', blank=True, null=True)
    id_producto = models.ForeignKey('productos.Productos', models.DO_NOTHING, db_column='id_producto', blank=True, null=True)
    cantidad = models.IntegerField(blank=True, null=True)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'detalles_compras'

    def __str__(self):
        return f"Detalle Compra {self.id_detalle_compra} - Compra: {self.id_compra} - Producto: {self.id_producto} - Cantidad: {self.cantidad} - Subtotal: {self.sub_total}"