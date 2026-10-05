from django.db import models

class Cajas(models.Model):
    id_caja = models.AutoField(primary_key=True)
    id_apertura = models.ForeignKey('empleados.Apertura', models.DO_NOTHING, db_column='id_apertura', blank=True, null=True)
    fecha_apertura = models.DateTimeField(blank=True, null=True)
    fecha_cierre = models.DateTimeField(blank=True, null=True)
    saldo_inicial = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    saldo_esperado = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    saldo_real = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    diferencia = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    estado = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cajas'

    def __str__(self):
        return f"Caja {self.id_caja} - Apertura: {self.id_apertura} - Estado: {'Abierta' if self.estado else 'Cerrada'}"

class MovimientosCaja(models.Model):
    id_movimiento_caja = models.AutoField(primary_key=True)
    id_pago_alquiler = models.ForeignKey('empleados.PagosAlquileres', models.DO_NOTHING, db_column='id_pago_alquiler', blank=True, null=True)
    id_pago_orden = models.ForeignKey('ventas.PagosOrden', models.DO_NOTHING, db_column='id_pago_orden', blank=True, null=True)
    id_compra = models.ForeignKey('compras.Compras', models.DO_NOTHING, db_column='id_compra', blank=True, null=True)
    id_caja = models.ForeignKey('cajas.Cajas', models.DO_NOTHING, db_column='id_caja', blank=True, null=True)
    importe = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fecha = models.DateTimeField(blank=True, null=True)
    tipo_movimiento = models.CharField(max_length=150, blank=True, null=True)
    concepto = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'movimientos_caja'
    def __str__(self):
        return f"Movimiento Caja {self.id_movimiento_caja} - Caja: {self.id_caja} - Importe: {self.importe} - Tipo: {self.tipo_movimiento} - compra: {self.id_compra} - Pago Orden: {self.id_pago_orden} - Pago Alquiler: {self.id_pago_alquiler}"