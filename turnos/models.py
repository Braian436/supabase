from django.db import models

class Turnos(models.Model):
    id_turno = models.BigAutoField(primary_key=True)
    fecha = models.DateField()
    hora = models.TimeField(blank=True, null=True)
    estado = models.CharField(blank=True, null=True)
    observacion = models.CharField(blank=True, null=True)
    # id_cliente = models.ForeignKey('Clientes', models.DO_NOTHING, db_column='id_cliente', blank=True, null=True)
    id_empleado = models.ForeignKey('empleados.Empleados', models.DO_NOTHING, db_column='id_empleado', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'turnos'

    def __str__(self):
        fecha_turno = self.fecha.strftime("%d/%m/%Y") if self.fecha else "Fecha no disponible"
        hora_turno = self.hora.strftime("%H:%M") if self.hora else "Hora no disponible"
        estado_turno = self.estado or "Estado no disponible"
        observacion_turno = self.observacion or "Sin observación"
        # cliente_turno = str(self.id_cliente) if self.id_cliente else "Cliente no asignado"
        empleado_turno = str(self.id_empleado) if self.id_empleado else "Empleado no asignado"
        #return f"Turno: {fecha_turno} {hora_turno} | Estado: {estado_turno} | Observación: {observacion_turno} | Cliente: {cliente_turno} | Empleado: {empleado_turno}"
        return f"Turno: {fecha_turno} {hora_turno} | Estado: {estado_turno} | Observación: {observacion_turno} | Empleado: {empleado_turno}"

class ServiciosTurnos(models.Model):
    id_servicio_turno = models.IntegerField(primary_key=True)
    orden = models.IntegerField(blank=True, null=True)
    id_servicio = models.ForeignKey('Servicios', models.DO_NOTHING, db_column='id_servicio', blank=True, null=True)
    id_turno = models.ForeignKey('Turnos', models.DO_NOTHING, db_column='id_turno', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'servicios_turnos'

    def __str__(self):
        orden_servicio = self.orden if self.orden is not None else "Orden no disponible"
        servicio = str(self.id_servicio) if self.id_servicio else "Servicio no asignado"
        turno = str(self.id_turno) if self.id_turno else "Turno no asignado"
        return f"Servicio Turno: Orden {orden_servicio} | Servicio: {servicio} | Turno: {turno}"

class Servicios(models.Model):
    id_servicio = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    descripcion = models.CharField(max_length=250, blank=True, null=True)
    estado = models.BooleanField(blank=True, null=True)
    precio = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    id_empleado = models.ForeignKey('empleados.Empleados', models.DO_NOTHING, db_column='id_empleado', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'servicios'

    def __str__(self):
        nombre_servicio = self.nombre or "Servicio sin nombre"
        descripcion_servicio = self.descripcion or "Sin descripción"
        estado_servicio = "Activo" if self.estado else "Inactivo"
        precio_servicio = f"${self.precio}" if self.precio is not None else "Precio no disponible"
        empleado_servicio = str(self.id_empleado) if self.id_empleado else "Empleado no asignado"
        return f"Servicio: {nombre_servicio} | Descripción: {descripcion_servicio} | Estado: {estado_servicio} | Precio: {precio_servicio} | Empleado: {empleado_servicio}"