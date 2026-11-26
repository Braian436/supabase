from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from cajas.models import Cajas, MovimientosCajas
from empleados.models import Empleados

from .serializers import (
    AbrirCajaSerializer,
    CajasSerializer,
    CerrarCajaSerializer,
    MovimientosCajasSerializer,
)


def autenticar_cajero(usuario, contrasena):
    """Valida credenciales contra auth_user y devuelve el empleado Cajero."""
    User = get_user_model()
    user = User.objects.filter(username=usuario, is_active=True).first()
    if not user or not user.check_password(contrasena):
        raise PermissionDenied('Usuario o contraseña incorrectos.')

    empleado = Empleados.objects.filter(id_user=user).first()
    if not empleado:
        raise PermissionDenied('El usuario no está vinculado a un empleado.')
    if not user.groups.filter(name__iexact='Cajero').exists():
        raise PermissionDenied('El usuario no tiene rol Cajero.')
    return empleado


def calcular_saldo_esperado(caja):
    """saldo_inicial + ingresos/cobros/propinas en efectivo − egresos."""
    saldo = caja.saldo_inicial or Decimal('0')
    for movimiento in MovimientosCajas.objects.filter(id_caja=caja):
        tipo = (movimiento.tipo_movimiento or '').lower()
        metodo = (movimiento.metodo_pago or 'efectivo').lower()
        if tipo in ('ingreso', 'cobro', 'propina'):
            if metodo == 'efectivo':
                saldo += movimiento.total
        elif tipo == 'anulacion':
            if metodo == 'efectivo':
                saldo -= movimiento.total
        elif tipo == 'egreso' and metodo == 'efectivo':
            saldo -= movimiento.total
    return saldo


class CajasViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CajasSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return (
            Cajas.objects.select_related('id_empleado')
            .order_by('-id_caja')
        )


class MovimientosCajasViewSet(viewsets.ModelViewSet):
    serializer_class = MovimientosCajasSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        queryset = MovimientosCajas.objects.all().order_by('-fecha')
        id_caja = self.request.query_params.get('id_caja')
        if id_caja:
            queryset = queryset.filter(id_caja_id=id_caja)
        return queryset

    def perform_create(self, serializer):
        caja = serializer.validated_data.get('id_caja')
        if caja is None:
            raise ValidationError({'id_caja': 'La caja es obligatoria.'})
        if not Cajas.objects.filter(
            pk=caja.pk, fecha_cierre__isnull=True
        ).exists():
            raise ValidationError({'id_caja': 'La caja está cerrada o no existe.'})
        serializer.save()


class AbrirCajaAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AbrirCajaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        empleado = autenticar_cajero(datos['usuario'], datos['contrasena'])

        if Cajas.objects.filter(fecha_cierre__isnull=True).exists():
            return Response(
                {'detail': 'Ya hay una caja abierta.'},
                status=status.HTTP_409_CONFLICT,
            )

        saldo_inicial = datos['saldo_inicial']
        with transaction.atomic():
            caja = Cajas.objects.create(
                id_empleado=empleado,
                fecha_inicio=timezone.now(),
                saldo_inicial=saldo_inicial,
                saldo_esperado=saldo_inicial,
            )
            MovimientosCajas.objects.create(
                id_caja=caja,
                total=saldo_inicial,
                fecha=timezone.now(),
                tipo_movimiento='apertura',
                concepto='Apertura de caja',
                metodo_pago='efectivo',
            )

        return Response(
            CajasSerializer(caja).data, status=status.HTTP_201_CREATED
        )


class CerrarCajaAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, pk):
        serializer = CerrarCajaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        empleado = autenticar_cajero(datos['usuario'], datos['contrasena'])

        with transaction.atomic():
            try:
                caja = Cajas.objects.select_for_update().get(pk=pk)
            except Cajas.DoesNotExist:
                raise NotFound('La caja no existe.')

            if caja.fecha_cierre is not None:
                return Response(
                    {'detail': 'La caja ya está cerrada.'},
                    status=status.HTTP_409_CONFLICT,
                )

            if caja.id_empleado_id != empleado.pk:
                raise PermissionDenied(
                    'Solo el cajero que abrió la caja puede cerrarla.'
                )

            esperado = calcular_saldo_esperado(caja)
            real = datos['saldo_real']
            caja.fecha_cierre = timezone.now()
            caja.saldo_esperado = esperado
            caja.saldo_real = real
            caja.diferencia = real - esperado
            caja.save(
                update_fields=[
                    'fecha_cierre',
                    'saldo_esperado',
                    'saldo_real',
                    'diferencia',
                ]
            )

        return Response(CajasSerializer(caja).data)
