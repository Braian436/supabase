from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny

from empleados.api.serializer import (
    BarberoPublicoSerializer,
    EmpleadosSerializer,
    LiquidacionesSemanalesSerializer,
)
from empleados.models import Empleados, LiquidacionesSemanales


class EmpleadosViewSet(viewsets.ModelViewSet):
    queryset = Empleados.objects.all().order_by('pk')
    serializer_class = EmpleadosSerializer
    permission_classes = [AllowAny]


class BarberosPublicosAPIView(generics.ListAPIView):
    serializer_class = BarberoPublicoSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return Empleados.objects.filter(id_rol__nombre='Barbero').order_by('pk')


class LiquidacionesSemanalesViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LiquidacionesSemanalesSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        liquidaciones = LiquidacionesSemanales.objects.all()
        return liquidaciones