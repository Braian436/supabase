from django.db import models


class Servicios(models.Model):
    id_servicio = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    precio = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'servicios'

    def __str__(self):
        precio_servicio = f"${self.precio}" if self.precio is not None else "Precio no disponible"
        return f"Servicio: {self.nombre} | Precio: {precio_servicio}"


class ServiciosTurnos(models.Model):
    id_servicio_turno = models.AutoField(primary_key=True)
    id_turno = models.ForeignKey(
        'turnos.Turnos',
        models.DO_NOTHING,
        db_column='id_turno',
        related_name='servicios_turnos',
    )
    id_servicio = models.ForeignKey(Servicios, models.DO_NOTHING, db_column='id_servicio')

    class Meta:
        db_table = 'servicios_turnos'

    def __str__(self):
        servicio = str(self.id_servicio) if self.id_servicio else "Servicio no asignado"
        turno = str(self.id_turno) if self.id_turno else "Turno no asignado"
        return f"Servicio Turno: Servicio: {servicio} | Turno: {turno}"


class EmpleadosServicios(models.Model):
    id_empleado_servicio = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey('empleados.Empleados', models.DO_NOTHING, db_column='id_empleado')
    id_servicio = models.ForeignKey(Servicios, models.DO_NOTHING, db_column='id_servicio')
    descripcion = models.CharField(max_length=100)

    class Meta:
        db_table = 'empleados_servicios'

    def __str__(self):
        empleado = str(self.id_empleado) if self.id_empleado else "Empleado no asignado"
        servicio = str(self.id_servicio) if self.id_servicio else "Servicio no asignado"
        return f"Empleado Servicio: Empleado: {empleado} | Servicio: {servicio}"
