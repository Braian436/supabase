from django.db import models


class Clientes(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    telefono = models.CharField(max_length=18)
    nombre = models.CharField(max_length=80)
    apellido = models.CharField(max_length=50)
    fecha_nacimiento = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clientes'

    def __str__(self):
        return f"{self.nombre} {self.apellido} - Tel: {self.telefono}"


class Turnos(models.Model):
    id_turno = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(Clientes, models.DO_NOTHING, db_column='id_cliente')
    id_empleado = models.ForeignKey('empleados.Empleados', models.DO_NOTHING, db_column='id_empleado')
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(max_length=25)

    class Meta:
        managed = False
        db_table = 'turnos'

    def __str__(self):
        fecha_turno = self.fecha.strftime("%d/%m/%Y") if self.fecha else "Fecha no disponible"
        hora_turno = self.hora.strftime("%H:%M") if self.hora else "Hora no disponible"
        estado_turno = self.estado or "Estado no disponible"
        cliente_turno = str(self.id_cliente) if self.id_cliente else "Cliente no asignado"
        empleado_turno = str(self.id_empleado) if self.id_empleado else "Empleado no asignado"
        return f"Turno: {fecha_turno} {hora_turno} | Estado: {estado_turno} | Cliente: {cliente_turno} | Empleado: {empleado_turno}"


class TurnosExpress(models.Model):
    id_express = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey('Clientes', models.DO_NOTHING, db_column='id_cliente')
    id_servicio = models.ForeignKey('servicios.Servicios', models.DO_NOTHING, db_column='id_servicio')
    id_empleado = models.ForeignKey('empleados.Empleados', models.DO_NOTHING, db_column='id_empleado')
    fecha = models.DateTimeField()
    hora = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.TextField()

    class Meta:
        managed = False
        db_table = 'turnos_express'

    def __str__(self):
        fecha_express = self.fecha.strftime("%d/%m/%Y") if self.fecha else "Fecha no disponible"
        hora_express = self.hora.strftime("%H:%M") if self.hora else "Hora no disponible"
        hora_fin_express = self.hora_fin.strftime("%H:%M") if self.hora_fin else "Hora no disponible"
        cliente_express = str(self.id_cliente) if self.id_cliente else "Cliente no asignado"
        empleado_express = str(self.id_empleado) if self.id_empleado else "Empleado no asignado"
        servicio_express = str(self.id_servicio) if self.id_servicio else "Servicio no asignado"
        return f"Turno Express: {fecha_express} {hora_express}-{hora_fin_express} | Cliente: {cliente_express} | Empleado: {empleado_express} | Servicio: {servicio_express}"
