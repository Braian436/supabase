from django.contrib.auth.models import Group
from django.db import transaction
from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny

from empleados.api.serializer import (
    BarberoPublicoSerializer,
    EmpleadosSerializer,
    GrupoUsuarioSerializer,
    LiquidacionesSemanalesSerializer,
    RolLaboralSerializer,
)
from empleados.models import EmpleadoCuenta, Empleados, LiquidacionesSemanales, Roles


class EmpleadosViewSet(viewsets.ModelViewSet):
    queryset = (
        Empleados.objects.select_related('id_rol', 'cuenta__usuario')
        .prefetch_related('cuenta__usuario__groups')
        .order_by('pk')
    )
    serializer_class = EmpleadosSerializer
    permission_classes = [AllowAny]

    def perform_destroy(self, instance):
        with transaction.atomic():
            cuenta = (
                EmpleadoCuenta.objects.select_related('usuario')
                .filter(empleado=instance)
                .first()
            )
            if cuenta is None:
                instance.delete()
                return

            usuario = cuenta.usuario
            usuario.is_active = False
            usuario.save(update_fields=['is_active'])
            instance.delete()


class RolesAPIView(generics.ListAPIView):
    queryset = Roles.objects.all().order_by('nombre')
    serializer_class = RolLaboralSerializer
    permission_classes = [AllowAny]
    pagination_class = None


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
        return Empleados.objects.filter(id_rol__nombre='Barbero').order_by('pk')


class LiquidacionesSemanalesViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LiquidacionesSemanalesSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        liquidaciones = LiquidacionesSemanales.objects.all()
        return liquidaciones