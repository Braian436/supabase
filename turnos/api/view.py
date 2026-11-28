from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from api.auth import empleado_de_usuario
from api.permissions import EsAdministrador, EsBarberoOAdministrador
from cajas.models import Cajas
from empleados.models import Empleados
from servicios.models import EmpleadosServicios, ServiciosTurnos
from turnos.models import Clientes, Turnos
from ventas.models import DetallesServicios, Ventas
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


def normalizar_telefono(valor):
    return ''.join(ch for ch in str(valor or '') if ch.isdigit())


def obtener_cliente_por_telefono(telefono):
    tel = normalizar_telefono(telefono)
    if not tel:
        return None
    telefono_raw = str(telefono or '').strip()
    candidatos = []
    for cliente in Clientes.objects.all().order_by('-id_cliente'):
        if normalizar_telefono(cliente.telefono) != tel:
            continue
        exacto = str(cliente.telefono or '').strip() == telefono_raw
        candidatos.append((exacto, cliente))
    if not candidatos:
        return None
    for exacto, cliente in candidatos:
        if exacto:
            return cliente
    return candidatos[0][1]


# ClientesViewSet definido más abajo (CRUD admin + búsqueda por teléfono).


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

        ids_servicios = list(dict.fromkeys([*data.get('servicios', []), *([data['id_servicio']] if data.get('id_servicio') else [])]))
        try:
            with transaction.atomic():
                empleado = Empleados.objects.select_for_update().get(pk=data['empleado'])

                occupied = Turnos.objects.filter(
                    id_empleado=empleado, fecha=data['fecha'], hora=data['hora'], estado__in=ESTADOS_OCUPADOS,
                ).exists()
                if occupied:
                    return api_error('slot_unavailable', 'El horario seleccionado ya está ocupado.', status.HTTP_409_CONFLICT)

                if ids_servicios:
                    asignados = set(
                        EmpleadosServicios.objects.filter(id_empleado=empleado, id_servicio_id__in=ids_servicios)
                        .values_list('id_servicio_id', flat=True)
                    )
                    faltantes = [sid for sid in ids_servicios if sid not in asignados]
                    if faltantes:
                        return api_error('invalid_service', 'El profesional no realiza uno de los servicios seleccionados.', status.HTTP_400_BAD_REQUEST)

                cliente = obtener_cliente_por_telefono(data['telefono'])
                email = (data.get('email') or '').strip() or None
                if cliente is None:
                    cliente = Clientes.objects.create(
                        telefono=data['telefono'], nombre=data['nombre'], apellido=data['apellido'], email=email
                    )
                elif email and not cliente.email:
                    cliente.email = email
                    cliente.save(update_fields=['email'])
                turno = Turnos.objects.create(
                    id_empleado=empleado, id_cliente=cliente, fecha=data['fecha'], hora=data['hora'], estado='pendiente',
                )
                for sid in ids_servicios:
                    ServiciosTurnos.objects.create(id_turno=turno, id_servicio_id=sid)
        except Empleados.DoesNotExist:
            return api_error('employee_not_found', 'No existe el empleado solicitado.', status.HTTP_404_NOT_FOUND)

        return Response({
            'id_turno': turno.pk, 'empleado': empleado.pk, 'cliente': cliente.pk,
            'fecha': turno.fecha.isoformat(), 'hora': turno.hora.strftime('%H:%M'), 'estado': turno.estado,
            'servicios': ids_servicios,
        }, status=status.HTTP_201_CREATED)


class ClientesViewSet(viewsets.ModelViewSet):
    queryset = Clientes.objects.all().order_by('nombre', 'apellido')
    serializer_class = ClientesSerializer
    pagination_class = None

    def get_permissions(self):
        if self.action in ('list', 'retrieve') and self.request.query_params.get('telefono'):
            return [AllowAny()]
        return [EsAdministrador()]

    def get_queryset(self):
        qs = Clientes.objects.all().order_by('nombre', 'apellido')
        telefono = self.request.query_params.get('telefono')
        if telefono:
            cliente = obtener_cliente_por_telefono(telefono)
            return qs.filter(pk=cliente.pk) if cliente else qs.none()
        return qs

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
        with transaction.atomic():
            turno = Turnos.objects.select_for_update().select_related('id_cliente', 'id_empleado').prefetch_related('servicios_turnos__id_servicio').get(pk=self.get_object().pk)
            if turno.estado.strip().casefold() != 'pendiente':
                return Response({'detail': 'Solo se pueden iniciar turnos pendientes.'}, status=status.HTTP_400_BAD_REQUEST)
            if not Cajas.objects.filter(fecha_cierre__isnull=True).exists():
                return Response({'detail': 'No hay una caja abierta para generar el ticket.'}, status=status.HTTP_409_CONFLICT)

            venta = Ventas.objects.select_for_update().filter(id_turno=turno, anulada=False).order_by('-id_venta').first()
            if venta is None:
                venta = Ventas.objects.create(
                    id_cliente=turno.id_cliente, id_turno=turno, estado=False, anulada=False,
                    fecha_venta=timezone.now(), fecha_cierre=timezone.now(), subtotal=0, descuento=0,
                )
            if not venta.estado and not venta.anulada:
                existentes = set(DetallesServicios.objects.filter(id_venta=venta).values_list('id_servicio_id', flat=True))
                total = venta.subtotal or 0
                for st in turno.servicios_turnos.all():
                    if st.id_servicio_id and st.id_servicio_id not in existentes:
                        precio = st.id_servicio.precio or 0
                        DetallesServicios.objects.create(
                            id_venta=venta, id_servicio_id=st.id_servicio_id, precio_unitario=precio, cantidad=1, importe=precio,
                        )
                        total += precio
                if total != (venta.subtotal or 0):
                    venta.subtotal = total
                    venta.save(update_fields=['subtotal'])

            turno.estado = 'en curso'
            turno.save(update_fields=['estado'])
        data = self.get_serializer(turno).data
        data['id_venta'] = venta.id_venta
        return Response(data)

    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        turno = self.get_object()
        if turno.estado.strip().casefold() != 'en curso':
            return Response({'detail': 'Solo se pueden finalizar turnos en curso.'}, status=status.HTTP_400_BAD_REQUEST)
        turno.estado = 'finalizado'
        turno.save(update_fields=['estado'])
        return Response(self.get_serializer(turno).data)
