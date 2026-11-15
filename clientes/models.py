from django.db import models

class Clientes(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    telefono = models.CharField()
    nombre = models.CharField()
    apellido = models.CharField()
    fecha_nacimiento = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clientes'
