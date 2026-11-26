from decimal import Decimal

from django.db import connection, transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from cajas.models import Cajas, MovimientosCajas
from productos.models import Productos
from servicios.models import Servicios
from turnos.models import Clientes
from ventas.models import DetallesProductos, DetallesServicios, Ventas

from .serializers import (
    CobrarVentaSerializer,
    CrearTicketSerializer,
    VentaSerializer,
)


def ventas_fecha_cierre_es_nullable():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT is_nullable FROM information_schema.columns "
            "WHERE table_name = 'ventas' AND column_name = 'fecha_cierre'"
        )
        fila = cursor.fetchone()
    return bool(fila and fila[0] == 'YES')


class VentasViewSet(viewsets.ModelViewSet):
    queryset = (
        Ventas.objects.select_related('id_cliente', 'id_turno')
        .prefetch_related('detallesproductos_set', 'detallesservicios_set')
        .order_by('-id_venta')
    )
    serializer_class = VentaSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    @action(detail=False, methods=['post'], url_path='crear-ticket')
    def crear_ticket(self, request):
        serializer = CrearTicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        cliente = self._obtener_cliente(datos)
        lineas_servicios = self._preparar_servicios(datos.get('servicios', []))
        lineas_productos = self._preparar_productos(datos.get('productos', []))
        descuento = datos.get('descuento') or Decimal('0')

        subtotal = sum(
            (importe for _, _, _, importe in lineas_servicios + lineas_productos),
            Decimal('0'),
        )
        if subtotal - descuento < 0:
            raise ValidationError({
                'descuento': 'El descuento supera el total del ticket.'
            })

        fecha_cierre = None if ventas_fecha_cierre_es_nullable() else timezone.now()

        with transaction.atomic():
            venta = Ventas.objects.create(
                id_cliente=cliente,
                estado=False,
                fecha_venta=timezone.now(),
                fecha_cierre=fecha_cierre,
                subtotal=subtotal,
                descuento=descuento,
            )

            for servicio, cantidad, precio, importe in lineas_servicios:
                DetallesServicios.objects.create(
                    id_venta=venta,
                    id_servicio=servicio,
                    precio_unitario=precio,
                    cantidad=cantidad,
                    importe=importe,
                )

            for producto, cantidad, precio, importe in lineas_productos:
                DetallesProductos.objects.create(
                    id_venta=venta,
                    id_producto=producto,
                    precio_unitario=precio,
                    cantidad=cantidad,
                    importe=importe,
                )
                Productos.objects.filter(pk=producto.pk).update(
                    stock_actual=F('stock_actual') - cantidad
                )

        return Response(VentaSerializer(venta).data, status=status.HTTP_201_CREATED)

    def _obtener_cliente(self, datos):
        id_cliente = datos.get('id_cliente')
        if id_cliente:
            try:
                return Clientes.objects.get(pk=id_cliente)
            except Clientes.DoesNotExist:
                raise ValidationError({'id_cliente': 'El cliente no existe.'})

        cliente_nuevo = datos.get('cliente')
        if not cliente_nuevo:
            raise ValidationError({
                'cliente': 'Indicá un cliente existente o uno nuevo.'
            })

        cliente, _ = Clientes.objects.get_or_create(
            telefono=cliente_nuevo['telefono'],
            defaults={
                'nombre': cliente_nuevo['nombre'],
                'apellido': cliente_nuevo['apellido'],
            },
        )
        return cliente

    def _preparar_servicios(self, items):
        lineas = []
        for item in items:
            try:
                servicio = Servicios.objects.get(pk=item['id_servicio'])
            except Servicios.DoesNotExist:
                raise ValidationError({
                    'servicios': f"El servicio {item['id_servicio']} no existe."
                })
            cantidad = item['cantidad']
            importe = servicio.precio * cantidad
            lineas.append((servicio, cantidad, servicio.precio, importe))
        return lineas

    def _preparar_productos(self, items):
        lineas = []
        for item in items:
            try:
                producto = Productos.objects.get(pk=item['id_producto'])
            except Productos.DoesNotExist:
                raise ValidationError({
                    'productos': f"El producto {item['id_producto']} no existe."
                })

            precio = (
                DetallesProductos.objects.filter(id_producto=producto)
                .order_by('-id_venta__fecha_venta', '-id_detalle_producto')
                .values_list('precio_unitario', flat=True)
                .first()
            )
            if precio is None:
                raise ValidationError({
                    'productos': (
                        f"El producto {producto.nombre} no tiene precio de venta "
                        "registrado."
                    ),
                })

            cantidad = item['cantidad']
            if producto.stock_actual < cantidad:
                raise ValidationError({
                    'productos': f"Stock insuficiente de {producto.nombre}."
                })

            importe = precio * cantidad
            lineas.append((producto, cantidad, precio, importe))
        return lineas

    @action(detail=True, methods=['post'])
    def cobrar(self, request, pk=None):
        serializer = CobrarVentaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        metodo = datos['metodo_pago']
        monto_recibido = datos.get('monto_recibido')

        with transaction.atomic():
            try:
                venta = Ventas.objects.select_for_update().get(pk=pk)
            except Ventas.DoesNotExist:
                raise NotFound('La venta no existe.')

            if venta.estado:
                return Response(
                    {'detail': 'La venta ya está cobrada.'},
                    status=status.HTTP_409_CONFLICT,
                )

            caja = (
                Cajas.objects.filter(fecha_cierre__isnull=True)
                .order_by('-id_caja')
                .first()
            )
            if caja is None:
                return Response(
                    {'detail': 'No hay una caja abierta.'},
                    status=status.HTTP_409_CONFLICT,
                )

            total = (venta.subtotal or Decimal('0')) - (
                venta.descuento or Decimal('0')
            )

            if metodo == 'efectivo':
                if monto_recibido is None or monto_recibido < total:
                    raise ValidationError({
                        'monto_recibido': (
                            'El monto recibido debe ser igual o mayor al total.'
                        ),
                    })
                vuelto = monto_recibido - total
                monto_recibido_final = monto_recibido
            else:
                vuelto = None
                monto_recibido_final = None

            venta.estado = True
            venta.fecha_cierre = timezone.now()
            venta.metodo_pago = metodo
            venta.monto_recibido = monto_recibido_final
            venta.vuelto = vuelto
            venta.save(
                update_fields=[
                    'estado',
                    'fecha_cierre',
                    'metodo_pago',
                    'monto_recibido',
                    'vuelto',
                ]
            )

            MovimientosCajas.objects.create(
                id_caja=caja,
                id_venta=venta,
                total=total,
                fecha=timezone.now(),
                tipo_movimiento='cobro',
                concepto=f'Venta #{venta.pk}',
                metodo_pago=metodo,
                monto_recibido=monto_recibido_final,
                vuelto=vuelto,
            )

        return Response(VentaSerializer(venta).data)
