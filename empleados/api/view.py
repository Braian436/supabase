from django.contrib.auth.models import Group
from django.db import transaction
from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny

from empleados.api.serializer import (
    BarberoPublicoSerializer,
    EmpleadosSerializer,
    GrupoUsuarioSerializer,
    LiquidacionesSemanalesSerializer,
)
from empleados.models import Empleados, LiquidacionesSemanales


class EmpleadosViewSet(viewsets.ModelViewSet):
    queryset = (
        Empleados.objects.select_related('id_user')
        .prefetch_related('id_user__groups')
        .order_by('pk')
    )
    serializer_class = EmpleadosSerializer
    permission_classes = [AllowAny]

    def perform_destroy(self, instance):
        with transaction.atomic():
            if instance.id_user is not None:
                instance.id_user.is_active = False
                instance.id_user.save(update_fields=['is_active'])
            instance.delete()


class GruposAPIView(generics.ListAPIView):
    queryset = Group.objects.all().order_by('name')
    serializer_class = GrupoUsuarioSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class BarberosPublicosAPIView(generics.ListAPIView):
    serializer_class = BarberoPublicoSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return Empleados.objects.filter(
            id_user__groups__name='Barberos',
        ).order_by('pk')


class LiquidacionesSemanalesViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LiquidacionesSemanalesSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        liquidaciones = LiquidacionesSemanales.objects.all()
        return liquidaciones