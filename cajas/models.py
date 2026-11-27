from django.db import models


class Cajas(models.Model):
    id_caja = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey('empleados.Empleados', models.DO_NOTHING, db_column='id_empleado')
    fecha_inicio = models.DateTimeField()
    fecha_cierre = models.DateTimeField(blank=True, null=True)
    saldo_inicial = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_esperado = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    saldo_real = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    diferencia = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'cajas'

    def __str__(self):
        return f"Caja {self.id_caja} - Apertura: {self.fecha_inicio} - Cierre: {self.fecha_cierre}"


class MovimientosCajas(models.Model):
    id_movimiento_caja = models.AutoField(primary_key=True)
    id_caja = models.ForeignKey(Cajas, models.DO_NOTHING, db_column='id_caja')
    id_venta = models.ForeignKey('ventas.Ventas', models.DO_NOTHING, db_column='id_venta', blank=True, null=True)
    id_compra = models.ForeignKey('compras.Compras', models.DO_NOTHING, db_column='id_compra', blank=True, null=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateTimeField()
    tipo_movimiento = models.CharField(max_length=150)
    concepto = models.CharField(max_length=200)
    metodo_pago = models.CharField(max_length=20, default='efectivo')
    monto_recibido = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    vuelto = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    id_express = models.ForeignKey('turnos.TurnosExpress', models.DO_NOTHING, db_column='id_express', blank=True, null=True)
    metodo_pago = models.CharField(max_length=50, blank=True, null=True)
    monto_recibido = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    vuelto = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'movimientos_cajas'

    def __str__(self):
        return f"Movimiento Caja {self.id_movimiento_caja} - Caja: {self.id_caja} - Total: {self.total} - Tipo: {self.tipo_movimiento}"
