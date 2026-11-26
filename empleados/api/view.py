from datetime import datetime, time, timedelta

from django.contrib.auth.models import Group
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import generics, status, viewsets
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
                id_user__groups__name__in=('Barbero', 'Barberos'),
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


class LiquidacionesSemanalesViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LiquidacionesSemanalesSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        liquidaciones = LiquidacionesSemanales.objects.all()
        request = getattr(self, 'request', None)
        empleado = request.query_params.get('empleado') if request is not None else None
        if empleado:
            liquidaciones = liquidaciones.filter(id_empleado_id=empleado)
        return liquidaciones
