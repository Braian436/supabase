from django.db import models


class Ventas(models.Model):
    id_venta = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey('turnos.Clientes', models.DO_NOTHING, db_column='id_cliente')
    id_turno = models.ForeignKey('turnos.Turnos', models.DO_NOTHING, db_column='id_turno')
    estado = models.BooleanField()
    fecha_venta = models.DateTimeField()
    fecha_cierre = models.DateTimeField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ventas'

    def __str__(self):
        return f"Venta {self.id_venta} - Cliente: {self.id_cliente} - Total: {self.subtotal}"


class DetallesProductos(models.Model):
    id_detalle_producto = models.AutoField(primary_key=True)
    id_venta = models.ForeignKey(Ventas, models.DO_NOTHING, db_column='id_venta')
    id_producto = models.ForeignKey('productos.Productos', models.DO_NOTHING, db_column='id_producto')
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad = models.IntegerField()
    importe = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'detalles_productos'

    def __str__(self):
        return f"Detalle Producto {self.id_detalle_producto} - Venta: {self.id_venta} - Producto: {self.id_producto} - Cantidad: {self.cantidad} - Importe: {self.importe}"


class DetallesServicios(models.Model):
    id_detalle_servicio = models.AutoField(primary_key=True)
    id_venta = models.ForeignKey(Ventas, models.DO_NOTHING, db_column='id_venta')
    id_servicio = models.ForeignKey('servicios.Servicios', models.DO_NOTHING, db_column='id_servicio')
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad = models.IntegerField()
    importe = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'detalles_servicios'

    def __str__(self):
        return f"Detalle Servicio {self.id_detalle_servicio} - Venta: {self.id_venta} - Servicio: {self.id_servicio} - Cantidad: {self.cantidad} - Importe: {self.importe}"
