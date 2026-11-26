from django.conf import settings
from django.db import models


class Empleados(models.Model):
    id_empleado = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True)
    foto_empleado = models.CharField(max_length=250, blank=True, null=True)
    porcentaje_comision = models.DecimalField(max_digits=5, decimal_places=2)
    id_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        models.DO_NOTHING,
        db_column='id_user',
        blank=True,
        null=True,
    )

    class Meta:
        managed = False
        db_table = 'empleados'

    def __str__(self):
        return f"{self.nombre} {self.apellido} (DNI: {self.dni})"


class RegistrosAsistencias(models.Model):
    id_asistencias = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey(Empleados, models.DO_NOTHING, db_column='id_empleado')
    fecha = models.DateTimeField()
    hora_entrada = models.TimeField(blank=True, null=True)
    hora_salida = models.TimeField()
    fecha_modificacion = models.DateTimeField()
    estado = models.CharField(max_length=20)
    observacion = models.CharField(max_length=200)

    class Meta:
        managed = False
        db_table = 'registros_asistencias'

    def __str__(self):
        return f"Registro de Asistencia: {self.id_empleado} - {self.fecha}"


class LiquidacionesSemanales(models.Model):
    id_liquidacion = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey(Empleados, models.DO_NOTHING, db_column='id_empleado')
    fecha_generacion = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    fecha_inicio = models.DateTimeField()
    total_comision = models.DecimalField(max_digits=12, decimal_places=2)
    total_a_pagar = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'liquidaciones_semanales'

    def __str__(self):
        return f"Liquidación Semanal: {self.id_empleado} - {self.fecha_generacion} | Total a Pagar: {self.total_a_pagar}"

