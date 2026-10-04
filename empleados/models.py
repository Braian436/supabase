from django.db import models

class Empleados(models.Model):
    id_empleado = models.IntegerField(primary_key=True)
    nombre_empleado = models.CharField(max_length=50, blank=True, null=True)
    foto_empleado = models.BinaryField(blank=True, null=True)
    dni = models.CharField(max_length=20, blank=True, null=True)
    password = models.CharField(max_length=150, blank=True, null=True)
    estado = models.CharField(max_length=20, blank=True, null=True)
    fecha_alta = models.DateTimeField(blank=True, null=True)
    ultimo_acceso = models.DateTimeField(blank=True, null=True)
    porcentaje_comision = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    id_rol = models.ForeignKey('empleados.Roles', models.DO_NOTHING, db_column='id_rol', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'empleados'

    def __str__(self):
        return f"{self.nombre_empleado} (DNI: {self.dni}) | Rol: {self.id_rol}"

class RegistrosDeAsistencias(models.Model):
    id_asistencia = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey('Empleados', models.DO_NOTHING, db_column='id_empleado', blank=True, null=True)
    fecha = models.DateField(blank=True, null=True)
    hora_entrada = models.TimeField(blank=True, null=True)
    hora_salida = models.TimeField(blank=True, null=True)
    fecha_modificacion = models.DateTimeField(blank=True, null=True)
    estado = models.CharField(max_length=20, blank=True, null=True)
    observaciones = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'registros_de_asistencias'

    def __str__(self):
        return f"Registro de Asistencia: {self.id_empleado} - {self.fecha}"

class Liquidaciones(models.Model):
    id_liquidacion = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey('Empleados', models.DO_NOTHING, db_column='id_empleado', blank=True, null=True)
    fecha_inicio = models.DateTimeField(blank=True, null=True)
    fecha_generacion = models.DateField(blank=True, null=True)
    total_comision = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_a_pagar = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    estado = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'liquidaciones'

    def __str__(self):
        return f"Liquidación: {self.id_empleado} - {self.fecha_generacion} | Total a Pagar: {self.total_a_pagar}"

class Roles(models.Model):
    id_rol = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=20, blank=True, null=True)
    descripcion = models.CharField(max_length=240, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'roles'

    def __str__(self):
        return f"Rol: {self.nombre} - {self.descripcion}"

class Alquileres(models.Model):
    id_alquiler = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey('Empleados', models.DO_NOTHING, db_column='id_empleado', blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    importe_acordado = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    estado = models.CharField(max_length=20, blank=True, null=True)
    observaciones = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'alquileres'

    def __str__(self):
        return f"Alquiler: {self.id_empleado} - {self.fecha_inicio} to {self.fecha_fin} | Importe: {self.importe_acordado}"

class PagosAlquileres(models.Model):
    id_pago_alquiler = models.AutoField(primary_key=True)
    id_alquiler = models.ForeignKey('Alquileres', models.DO_NOTHING, db_column='id_alquiler', blank=True, null=True)
    fecha = models.DateTimeField(blank=True, null=True)
    importe = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    estado = models.BooleanField(blank=True, null=True)
    medio_pago = models.CharField(max_length=30, blank=True, null=True)
    observaciones = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pagos_alquileres'

    def __str__(self):
        return f"Pago Alquiler: {self.id_alquiler} - {self.fecha} | Importe: {self.importe} | Estado: {'Pagado' if self.estado else 'Pendiente'}"

class Apertura(models.Model):
    id_apertura = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey('Empleados', models.DO_NOTHING, db_column='id_empleado', blank=True, null=True)
    fecha_hora = models.DateTimeField(blank=True, null=True)
    turno = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'apertura'

    def __str__(self):
        return f"Apertura: {self.id_empleado} - {self.fecha_hora} | Turno: {self.turno}"