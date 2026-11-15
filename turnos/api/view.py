from datetime import timedelta

from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from empleados.models import Empleados
from turnos.models import Clientes, Turnos
from turnos.api.serializer import (
    DisponibilidadQuerySerializer,
    ReservaTurnoSerializer,
)


ESTADOS_OCUPADOS = ('pendiente', 'en curso', 'finalizado')


def api_error(code, detail, http_status):
    return Response(
        {'error': {'code': code, 'detail': detail}},
        status=http_status,
    )


class DisponibilidadTurnosAPIView(APIView):
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
        current_date = data['desde']
        while current_date <= data['hasta']:
            for hour in sorted(data['horas']):
                is_available = (current_date, hour) not in occupied
                slots.append({
                    'fecha': current_date.isoformat(),
                    'hora': hour.strftime('%H:%M'),
                    'estado': 'disponible' if is_available else 'ocupado',
                    'disponible': is_available,
                })
            current_date += timedelta(days=1)

        return Response({
            'empleado': data['empleado'],
            'desde': data['desde'].isoformat(),
            'hasta': data['hasta'].isoformat(),
            'slots': slots,
        })


class ReservarTurnoAPIView(APIView):
    def post(self, request):
        serializer = ReservaTurnoSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                'validation_error',
                serializer.errors,
                status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
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
