from django.db import models

class Ordenes(models.Model):
    id_orden = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey('clientes.Clientes', models.DO_NOTHING, db_column='id_cliente', blank=True, null=True)
    id_empleado = models.ForeignKey('empleados.Empleados', models.DO_NOTHING, db_column='id_empleado', blank=True, null=True)
    fecha_apertura = models.DateTimeField(blank=True, null=True)
    fecha_cierre = models.DateTimeField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    descuentos = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    total_final = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    observaciones = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ordenes'

    def __str__(self):
        return f"Orden {self.id_orden} - Cliente: {self.id_cliente} - Total: {self.total_final}"

class PagosOrden(models.Model):
    id_pago_orden = models.AutoField(primary_key=True)
    id_orden = models.ForeignKey('Ordenes', models.DO_NOTHING, db_column='id_orden', blank=True, null=True)
    fecha = models.DateTimeField(blank=True, null=True)
    importe = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    estado = models.BooleanField(blank=True, null=True)
    medio_pago = models.CharField(max_length=30, blank=True, null=True)
    observaciones = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pagos_orden'
    
    def __str__(self):
        return f"Pago {self.id_pago_orden} - Orden: {self.id_orden} - Importe: {self.importe}"

class DetalleServicios(models.Model):
    id_detalle_servicio = models.AutoField(primary_key=True)
    id_orden = models.ForeignKey('Ordenes', models.DO_NOTHING, db_column='id_orden', blank=True, null=True)
    id_servicio = models.ForeignKey('turnos.Servicios', models.DO_NOTHING, db_column='id_servicio', blank=True, null=True)
    precio_actual = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'detalle_servicios'

    def __str__(self):
        return f"Detalle Servicio {self.id_detalle_servicio} - Orden: {self.id_orden} - Servicio: {self.id_servicio} - Subtotal: {self.sub_total}"

class DetalleProductos(models.Model):
    id_detalle_producto = models.AutoField(primary_key=True)
    id_orden = models.ForeignKey('Ordenes', models.DO_NOTHING, db_column='id_orden', blank=True, null=True)
    id_producto = models.ForeignKey('productos.Productos', models.DO_NOTHING, db_column='id_producto', blank=True, null=True)
    cantidad = models.IntegerField(blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'detalle_productos'

    def __str__(self):
        return f"Detalle Producto {self.id_detalle_producto} - Orden: {self.id_orden} - Producto: {self.id_producto} - Cantidad: {self.cantidad} - Subtotal: {self.sub_total}"

