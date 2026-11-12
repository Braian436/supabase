from rest_framework import viewsets
from empleados.models import Empleados
from empleados.api.serializer import EmpleadosSerializaer

class EmpleadosViewSet(viewsets.ModelViewSet):
    queryset= Empleados.objects.all()
    
    serializer_class= EmpleadosSerializaer