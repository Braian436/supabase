from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from servicios.api.serializer import ServiciosSerializer
from servicios.models import Servicios


class ServiciosViewSet(viewsets.ModelViewSet):
    queryset = Servicios.objects.all().order_by('nombre')
    serializer_class = ServiciosSerializer
    permission_classes = [AllowAny]
    pagination_class = None
