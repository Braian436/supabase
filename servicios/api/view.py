from rest_framework import viewsets

from api.permissions import AdministradorOLectura
from servicios.api.serializer import EmpleadosServiciosSerializer, ServiciosSerializer
from servicios.models import EmpleadosServicios, Servicios


class ServiciosViewSet(viewsets.ModelViewSet):
    queryset = Servicios.objects.all().order_by('nombre')
    serializer_class = ServiciosSerializer
    permission_classes = [AdministradorOLectura]
    pagination_class = None

    def perform_destroy(self, instance):
        EmpleadosServicios.objects.filter(id_servicio=instance).delete()
        instance.delete()


class EmpleadosServiciosViewSet(viewsets.ModelViewSet):
    queryset = EmpleadosServicios.objects.all()
    serializer_class = EmpleadosServiciosSerializer
    permission_classes = [AdministradorOLectura]
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        id_servicio = self.request.query_params.get('id_servicio')
        return queryset.filter(id_servicio=id_servicio) if id_servicio else queryset
