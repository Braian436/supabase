from django.db import models

class Clientes(models.Model):
    id_cliente = models.BigAutoField(primary_key=True)
    telefono = models.CharField()
    estado = models.BooleanField(blank=True, null=True)
    nombre = models.CharField(blank=True, null=True)
    apellido = models.CharField(blank=True, null=True)
    email = models.CharField(unique=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clientes'

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.email}"