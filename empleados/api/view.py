from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from cajas.models import Cajas
from api.permissions import EsAdministrador
from empleados.api.serializer import (
    BarberoPublicoSerializer,
    EmpleadosSerializer,
    GrupoUsuarioSerializer,
    LiquidacionesSemanalesSerializer,
    RegistrosAsistenciasSerializer,
)
from empleados.models import Empleados, LiquidacionesSemanales, RegistrosAsistencias
from servicios.models import ServiciosTurnos
from turnos.models import Turnos, TurnosExpress
from ventas.models import DetallesServicios, Ventas


def hay_caja_abierta():
    return Cajas.objects.filter(fecha_cierre__isnull=True).exists()


def rango_dia(fecha):
    """Devuelve el inicio y el fin (exclusivo) del día en la zona horaria local."""
    inicio_local = datetime.combine(fecha, time.min)
    zona = timezone.get_current_timezone()
    inicio = timezone.make_aware(inicio_local, zona)
    return inicio, inicio + timedelta(days=1)


def fecha_consulta(request):
    texto = request.query_params.get('fecha')
    if not texto:
        return timezone.localdate()
    fecha = parse_date(texto)
    if fecha is None:
        raise ValidationError({'fecha': 'Formato inválido. Usá YYYY-MM-DD.'})
    return fecha



class EmpleadosViewSet(viewsets.ModelViewSet):
    queryset = (
        Empleados.objects.select_related('id_user')
        .prefetch_related('id_user__groups')
        .order_by('pk')
    )
    serializer_class = EmpleadosSerializer
    permission_classes = [EsAdministrador]

    def perform_destroy(self, instance):
        with transaction.atomic():
            if instance.id_user is not None:
                instance.id_user.is_active = False
                instance.id_user.save(update_fields=['is_active'])
            instance.delete()


class GruposAPIView(generics.ListAPIView):
    queryset = Group.objects.all().order_by('name')
    serializer_class = GrupoUsuarioSerializer
    permission_classes = [EsAdministrador]
    pagination_class = None


class BarberosPublicosAPIView(generics.ListAPIView):
    serializer_class = BarberoPublicoSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return (
            Empleados.objects.filter(
                id_user__groups__name__in=('Barbero', 'Barberos', 'Administrador'),
            )
            .distinct()
            .order_by('pk')
        )


class AsistenciasDiaAPIView(APIView):
    """Lista todos los empleados con su asistencia del día indicado."""

    permission_classes = [AllowAny]

    def get(self, request):
        fecha = fecha_consulta(request)
        inicio, fin = rango_dia(fecha)

        empleados = (
            Empleados.objects.select_related('id_user')
            .prefetch_related('id_user__groups')
            .order_by('apellido', 'nombre')
        )
        registros = RegistrosAsistencias.objects.filter(
            fecha__gte=inicio,
            fecha__lt=fin,
        )
        por_empleado = {
            registro.id_empleado_id: registro for registro in registros
        }

        filas = []
        for empleado in empleados:
            registro = por_empleado.get(empleado.id_empleado)
            usuario = empleado.id_user
            grupo = usuario.groups.first() if usuario else None
            filas.append({
                'id_empleado': empleado.id_empleado,
                'nombre': empleado.nombre,
                'apellido': empleado.apellido,
                'rol': grupo.name if grupo else '',
                'id_asistencias': registro.id_asistencias if registro else None,
                'hora_entrada': (
                    registro.hora_entrada.strftime('%H:%M')
                    if registro and registro.hora_entrada
                    else None
                ),
                'hora_salida': (
                    registro.hora_salida.strftime('%H:%M')
                    if registro and registro.hora_salida
                    else None
                ),
                'estado': registro.estado if registro else None,
                'observacion': registro.observacion if registro else '',
            })

        resumen = {
            'total': len(filas),
            'presentes': sum(fila['estado'] == 'presente' for fila in filas),
            'ausentes': sum(fila['estado'] == 'ausente' for fila in filas),
            'justificados': sum(
                fila['estado'] == 'justificado' for fila in filas
            ),
            'sin_registrar': sum(fila['estado'] is None for fila in filas),
        }
        return Response({
            'fecha': fecha.isoformat(),
            'asistencias': filas,
            'resumen': resumen,
        })


class RegistrosAsistenciasViewSet(viewsets.ModelViewSet):
    queryset = (
        RegistrosAsistencias.objects.select_related('id_empleado')
        .order_by('-fecha')
    )
    serializer_class = RegistrosAsistenciasSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list' or self.request.query_params.get('fecha'):
            inicio, fin = rango_dia(fecha_consulta(self.request))
            queryset = queryset.filter(fecha__gte=inicio, fecha__lt=fin)

        id_empleado = self.request.query_params.get('id_empleado')
        if id_empleado:
            queryset = queryset.filter(id_empleado_id=id_empleado)
        return queryset

    def create(self, request, *args, **kwargs):
        if not hay_caja_abierta():
            return Response(
                {'detail': 'No hay una caja abierta.'},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data
        empleado = datos['id_empleado']
        estado = datos.get('estado') or 'presente'

        hoy = timezone.localdate()
        inicio, fin = rango_dia(hoy)
        if RegistrosAsistencias.objects.filter(
            id_empleado=empleado,
            fecha__gte=inicio,
            fecha__lt=fin,
        ).exists():
            return Response(
                {'detail': 'Ese empleado ya tiene una asistencia registrada hoy.'},
                status=status.HTTP_409_CONFLICT,
            )

        ahora = timezone.now()
        hora_actual = timezone.localtime(ahora).time().replace(microsecond=0)
        hora_entrada = datos.get('hora_entrada')
        if estado != 'ausente' and hora_entrada is None:
            hora_entrada = hora_actual

        registro = RegistrosAsistencias.objects.create(
            id_empleado=empleado,
            fecha=ahora,
            hora_entrada=hora_entrada,
            hora_salida=datos.get('hora_salida'),
            fecha_modificacion=ahora,
            estado=estado,
            observacion=datos.get('observacion', ''),
        )
        salida = self.get_serializer(registro)
        return Response(salida.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        if not hay_caja_abierta():
            return Response(
                {'detail': 'No hay una caja abierta.'},
                status=status.HTTP_409_CONFLICT,
            )
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(fecha_modificacion=timezone.now())


ESTADOS_FINALIZADOS = {
    'finalizado', 'completado', 'realizado', 'atendido', 'asistio', 'done', 'finished', 'completed',
}


def _normalizar_estado(valor):
    return str(valor or '').strip().casefold()


def _parse_fecha(valor, nombre):
    if not valor:
        raise ValidationError({nombre: 'Este campo es requerido.'})
    dt = parse_datetime(str(valor))
    if dt is None:
        d = parse_date(str(valor))
        if d is None:
            raise ValidationError({nombre: 'Formato inválido.'})
        dt = datetime.combine(d, time.min)
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _calcular_liquidacion(empleado, inicio, fin):
    if fin < inicio:
        raise ValidationError({'fecha_fin': 'Debe ser posterior a fecha_inicio.'})
    turnos_ids = list(
        Turnos.objects.filter(id_empleado=empleado, fecha__gte=inicio.date(), fecha__lte=fin.date())
        .values_list('id_turno', 'estado')
    )
    finalizados_ids = [tid for tid, est in turnos_ids if _normalizar_estado(est) in ESTADOS_FINALIZADOS]
    servicios_turnos = ServiciosTurnos.objects.filter(id_turno_id__in=finalizados_ids).count() if finalizados_ids else 0
    if servicios_turnos == 0:
        servicios_turnos = len(finalizados_ids)

    express = TurnosExpress.objects.filter(id_empleado=empleado, fecha__gte=inicio, fecha__lte=fin).values('estado')
    servicios_express = sum(1 for t in express if _normalizar_estado(t['estado']) in ESTADOS_FINALIZADOS)
    cantidad_servicios = servicios_turnos + servicios_express

    ventas = Ventas.objects.filter(
        Q(id_turno__id_empleado=empleado) | Q(id_express__id_empleado=empleado),
        fecha_venta__gte=inicio, fecha_venta__lte=fin, estado=True, anulada=False,
    )
    base = Decimal('0')
    for v in ventas:
        base += Decimal(str(v.subtotal or 0)) - Decimal(str(v.descuento or 0))
    if base < 0:
        base = Decimal('0')
    porcentaje = Decimal(str(empleado.porcentaje_comision or 0))
    total_comision = (base * porcentaje / Decimal('100')).quantize(Decimal('0.01'))
    return {
        'id_empleado': empleado.id_empleado,
        'empleado_nombre': empleado.nombre,
        'empleado_apellido': empleado.apellido,
        'porcentaje_comision': str(porcentaje),
        'fecha_inicio': inicio.isoformat(),
        'fecha_fin': fin.isoformat(),
        'cantidad_servicios': cantidad_servicios,
        'base': str(base.quantize(Decimal('0.01'))),
        'total_comision': str(total_comision),
        'total_a_pagar': str(total_comision),
    }


class LiquidacionesSemanalesViewSet(viewsets.ModelViewSet):
    serializer_class = LiquidacionesSemanalesSerializer
    permission_classes = [EsAdministrador]

    def get_queryset(self):
        qs = LiquidacionesSemanales.objects.select_related('id_empleado').order_by('-fecha_inicio', '-id_liquidacion')
        params = self.request.query_params
        empleado = params.get('empleado') or params.get('id_empleado')
        if empleado:
            qs = qs.filter(id_empleado_id=empleado)
        estado = params.get('estado')
        if estado in ('true', 'false', '1', '0'):
            qs = qs.filter(estado=estado in ('true', '1'))
        return qs

    def perform_create(self, serializer):
        serializer.save(fecha_generacion=timezone.now())

    @action(detail=False, methods=['post'], url_path='calcular')
    def calcular(self, request):
        empleado_id = request.data.get('id_empleado')
        if not empleado_id:
            raise ValidationError({'id_empleado': 'Este campo es requerido.'})
        try:
            empleado = Empleados.objects.get(pk=empleado_id)
        except Empleados.DoesNotExist:
            raise ValidationError({'id_empleado': 'Empleado no encontrado.'})
        inicio = _parse_fecha(request.data.get('fecha_inicio'), 'fecha_inicio')
        fin = _parse_fecha(request.data.get('fecha_fin'), 'fecha_fin')
        return Response(_calcular_liquidacion(empleado, inicio, fin))
