from datetime import timedelta

from django.db import IntegrityError, transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from api.auth import empleado_de_usuario
from api.permissions import EsAdministrador, EsBarberoOAdministrador
from empleados.models import Empleados
from turnos.models import Clientes, Turnos
from turnos.api.serializer import (
    ClientesSerializer,
    DisponibilidadQuerySerializer,
    ReservaTurnoSerializer,
    TurnosSerializer,
)
from turnos.api.horarios import (
    es_dia_habil,
    es_reservable,
    hora_limite,
    momento_del_slot,
)


ESTADOS_OCUPADOS = ('pendiente', 'en curso', 'finalizado')


class ClientesViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ClientesSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return Clientes.objects.all().order_by('nombre', 'apellido')


def api_error(code, detail, http_status):
    return Response(
        {'error': {'code': code, 'detail': detail}},
        status=http_status,
    )


class DisponibilidadTurnosAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.copy()
        query.setlist('horas', request.query_params.getlist('horas'))
        serializer = DisponibilidadQuerySerializer(data=query)
        if not serializer.is_valid():
            return api_error(
                'validation_error',
                serializer.errors,
                status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        if not Empleados.objects.filter(pk=data['empleado']).exists():
            return api_error(
                'employee_not_found',
                'No existe el empleado solicitado.',
                status.HTTP_404_NOT_FOUND,
            )

        occupied = set(
            Turnos.objects.filter(
                id_empleado_id=data['empleado'],
                fecha__range=(data['desde'], data['hasta']),
                hora__in=data['horas'],
                estado__in=ESTADOS_OCUPADOS,
            ).values_list('fecha', 'hora')
        )

        slots = []
        limite = hora_limite()
        current_date = data['desde']
        while current_date <= data['hasta']:
            for hour in sorted(data['horas']):
                dia_habil = es_dia_habil(current_date)
                dentro_del_margen = dia_habil and (
                    momento_del_slot(current_date, hour) >= limite
                )
                is_available = (
                    (current_date, hour) not in occupied and dentro_del_margen
                )
                if not dia_habil:
                    motivo = 'dia_cerrado'
                elif not dentro_del_margen:
                    motivo = 'hora_no_disponible'
                elif not is_available:
                    motivo = 'ocupado'
                else:
                    motivo = None
                slots.append({
                    'fecha': current_date.isoformat(),
                    'hora': hour.strftime('%H:%M'),
                    'estado': 'disponible' if is_available else 'ocupado',
                    'disponible': is_available,
                    'motivo': motivo,
                })
            current_date += timedelta(days=1)

        return Response({
            'empleado': data['empleado'],
            'desde': data['desde'].isoformat(),
            'hasta': data['hasta'].isoformat(),
            'slots': slots,
        })


class ReservarTurnoAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ReservaTurnoSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                'validation_error',
                serializer.errors,
                status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        if not es_dia_habil(data['fecha']):
            return api_error(
                'dia_no_habil',
                'Los domingos no se atiende. Elegí otro día.',
                status.HTTP_409_CONFLICT,
            )

        if not es_reservable(data['fecha'], data['hora']):
            return api_error(
                'hora_no_disponible',
                'El horario ya pasó o tiene menos de 5 minutos de '
                'anticipación. Elegí otro.',
                status.HTTP_409_CONFLICT,
            )

        try:
            with transaction.atomic():
                empleado = Empleados.objects.select_for_update().get(
                    pk=data['empleado']
                )

                occupied = Turnos.objects.filter(
                    id_empleado=empleado,
                    fecha=data['fecha'],
                    hora=data['hora'],
                    estado__in=ESTADOS_OCUPADOS,
                ).exists()
                if occupied:
                    return api_error(
                        'slot_unavailable',
                        'El horario seleccionado ya está ocupado.',
                        status.HTTP_409_CONFLICT,
                    )

                cliente, _ = Clientes.objects.get_or_create(
                    telefono=data['telefono'],
                    defaults={
                        'nombre': data['nombre'],
                        'apellido': data['apellido'],
                    },
                )
                turno = Turnos.objects.create(
                    id_empleado=empleado,
                    id_cliente=cliente,
                    fecha=data['fecha'],
                    hora=data['hora'],
                    estado='pendiente',
                )
        except Empleados.DoesNotExist:
            return api_error(
                'employee_not_found',
                'No existe el empleado solicitado.',
                status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                'id_turno': turno.pk,
                'empleado': empleado.pk,
                'cliente': cliente.pk,
                'fecha': turno.fecha.isoformat(),
                'hora': turno.hora.strftime('%H:%M'),
                'estado': turno.estado,
            },
            status=status.HTTP_201_CREATED,
        )


class ClientesViewSet(viewsets.ModelViewSet):
    queryset = Clientes.objects.all().order_by('nombre', 'apellido')
    serializer_class = ClientesSerializer
    permission_classes = [EsAdministrador]
    pagination_class = None

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except IntegrityError as exc:
            raise ValidationError('No se puede eliminar el cliente porque tiene turnos o ventas asociadas.') from exc


class TurnosViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TurnosSerializer
    permission_classes = [EsBarberoOAdministrador]
    pagination_class = None

    def get_queryset(self):
        usuario = self.request.user
        queryset = (
            Turnos.objects.select_related('id_cliente', 'id_empleado')
            .prefetch_related('servicios_turnos__id_servicio')
        )

        if usuario is not None and usuario.groups.filter(name='Barbero').exists():
            empleado = empleado_de_usuario(usuario)
            if empleado is None:
                return queryset.none()
            queryset = queryset.filter(id_empleado=empleado)

        params = self.request.query_params
        empleado = params.get('empleado')
        if empleado:
            queryset = queryset.filter(id_empleado_id=empleado)
        if params.get('fecha'):
            queryset = queryset.filter(fecha=params['fecha'])
        if params.get('desde'):
            queryset = queryset.filter(fecha__gte=params['desde'])
        if params.get('hasta'):
            queryset = queryset.filter(fecha__lte=params['hasta'])
        if params.get('estado'):
            queryset = queryset.filter(estado__iexact=params['estado'])

        return queryset.order_by('fecha', 'hora')

    @action(detail=True, methods=['post'])
    def iniciar(self, request, pk=None):
        turno = self.get_object()
        if turno.estado.strip().casefold() != 'pendiente':
            return Response(
                {'detail': 'Solo se pueden iniciar turnos pendientes.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        turno.estado = 'en curso'
        turno.save(update_fields=['estado'])
        return Response(self.get_serializer(turno).data)
