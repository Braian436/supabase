from decimal import Decimal

from django.db import connection, transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.permissions import EsAdministradorOCajero
from cajas.api.views import autenticar_cajero
from cajas.models import Cajas, MovimientosCajas
from productos.models import Productos
from servicios.models import Servicios
from turnos.models import Clientes
from ventas.models import DetallesProductos, DetallesServicios, Ventas

from .serializers import (
    AgregarItemVentaSerializer,
    AnularVentaSerializer,
    CancelarVentaSerializer,
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
    http_method_names = ['get', 'post', 'head', 'options']

    def create(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Las ventas se crean desde un ticket.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @staticmethod
    def _reponer_stock(venta):
        for detalle in DetallesProductos.objects.filter(id_venta=venta):
            Productos.objects.filter(pk=detalle.id_producto_id).update(
                stock_actual=F('stock_actual') + detalle.cantidad
            )

    @action(detail=True, methods=['post'], url_path='anular')
    def anular(self, request, pk=None):
        serializer = AnularVentaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data
        empleado = autenticar_cajero(datos['usuario'], datos['contrasena'])

        with transaction.atomic():
            venta = Ventas.objects.select_for_update().filter(pk=pk).first()
            if venta is None:
                raise NotFound('La venta no existe.')
            if venta.anulada:
                return Response(
                    {'detail': 'La venta ya está anulada.'},
                    status=status.HTTP_409_CONFLICT,
                )
            if not venta.estado:
                return Response(
                    {
                        'detail': (
                            'Solo se anulan ventas cobradas. '
                            'Para un ticket pendiente usá cancelar.'
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            movimiento = (
                MovimientosCajas.objects.select_related('id_caja')
                .filter(id_venta=venta, tipo_movimiento__iexact='cobro')
                .order_by('-id_movimiento_caja')
                .first()
            )
            if movimiento is None or movimiento.id_caja is None:
                return Response(
                    {'detail': 'La venta no está asociada a una caja.'},
                    status=status.HTTP_409_CONFLICT,
                )

            caja = movimiento.id_caja
            if caja.fecha_cierre is not None:
                return Response(
                    {
                        'detail': (
                            'La caja ya está cerrada. '
                            'Registrá una devolución.'
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            if caja.id_empleado_id != empleado.pk:
                raise PermissionDenied(
                    'Solo el cajero que abrió la caja puede anular ventas.'
                )

            motivo = datos['motivo'].strip()
            ahora = timezone.now()
            MovimientosCajas.objects.create(
                id_caja=caja,
                id_venta=venta,
                total=movimiento.total,
                fecha=ahora,
                tipo_movimiento='anulacion',
                concepto=f'Anulación venta #{venta.pk}: {motivo}',
                metodo_pago=movimiento.metodo_pago or 'efectivo',
            )
            self._reponer_stock(venta)
            venta.anulada = True
            venta.motivo_anulacion = motivo
            venta.anulada_por = (
                empleado.id_user.get_username()
                if empleado.id_user_id
                else datos['usuario']
            )
            venta.fecha_anulacion = ahora
            venta.save(
                update_fields=[
                    'anulada',
                    'motivo_anulacion',
                    'anulada_por',
                    'fecha_anulacion',
                ]
            )

        return Response(VentaSerializer(venta).data)

    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar(self, request, pk=None):
        serializer = CancelarVentaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        motivo = serializer.validated_data['motivo'].strip()

        with transaction.atomic():
            venta = Ventas.objects.select_for_update().filter(pk=pk).first()
            if venta is None:
                raise NotFound('La venta no existe.')
            if venta.anulada:
                return Response(
                    {'detail': 'La venta ya está anulada.'},
                    status=status.HTTP_409_CONFLICT,
                )
            if venta.estado:
                return Response(
                    {'detail': 'La venta ya está cobrada: usá anular.'},
                    status=status.HTTP_409_CONFLICT,
                )

            caja = (
                Cajas.objects.select_related('id_empleado__id_user')
                .filter(fecha_cierre__isnull=True)
                .order_by('-id_caja')
                .first()
            )
            if caja is None:
                return Response(
                    {'detail': 'No hay una caja abierta.'},
                    status=status.HTTP_409_CONFLICT,
                )

            usuario = getattr(caja.id_empleado, 'id_user', None)
            ahora = timezone.now()
            self._reponer_stock(venta)
            venta.anulada = True
            venta.motivo_anulacion = motivo
            venta.anulada_por = (
                usuario.get_username() if usuario else 'Caja'
            )
            venta.fecha_anulacion = ahora
            venta.save(
                update_fields=[
                    'anulada',
                    'motivo_anulacion',
                    'anulada_por',
                    'fecha_anulacion',
                ]
            )

        return Response(VentaSerializer(venta).data)

    @action(detail=True, methods=['post'], url_path='agregar-item', permission_classes=[EsAdministradorOCajero])
    def agregar_item(self, request, pk=None):
        if not Cajas.objects.filter(fecha_cierre__isnull=True).exists():
            return Response({'detail': 'No hay una caja abierta.'}, status=status.HTTP_409_CONFLICT)
        serializer = AgregarItemVentaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data
        with transaction.atomic():
            venta = Ventas.objects.select_for_update().filter(pk=pk).first()
            if venta is None:
                raise NotFound('La venta no existe.')
            if venta.anulada or venta.estado:
                return Response({'detail': 'Solo se pueden editar tickets pendientes.'}, status=status.HTTP_409_CONFLICT)
            if datos['tipo'] == 'servicio':
                servicio = Servicios.objects.filter(pk=datos['id_item']).first()
                if not servicio:
                    raise ValidationError({'id_item': 'El servicio no existe.'})
                DetallesServicios.objects.create(
                    id_venta=venta, id_servicio=servicio, precio_unitario=servicio.precio,
                    cantidad=datos['cantidad'], importe=servicio.precio * datos['cantidad'],
                )
            else:
                producto = Productos.objects.select_for_update().filter(pk=datos['id_item']).first()
                if not producto:
                    raise ValidationError({'id_item': 'El producto no existe.'})
                precio = (
                    DetallesProductos.objects.filter(id_producto=producto)
                    .order_by('-id_venta__fecha_venta', '-id_detalle_producto')
                    .values_list('precio_unitario', flat=True).first()
                )
                if precio is None:
                    raise ValidationError({'id_item': f'El producto {producto.nombre} no tiene precio de venta registrado.'})
                cantidad = datos['cantidad']
                if producto.stock_actual < cantidad:
                    raise ValidationError({'cantidad': f'Stock insuficiente de {producto.nombre}.'})
                DetallesProductos.objects.create(
                    id_venta=venta, id_producto=producto, precio_unitario=precio,
                    cantidad=cantidad, importe=precio * cantidad,
                )
                Productos.objects.filter(pk=producto.pk).update(stock_actual=F('stock_actual') - cantidad)
            total_serv = sum((d.importe for d in DetallesServicios.objects.filter(id_venta=venta)), Decimal('0'))
            total_prod = sum((d.importe for d in DetallesProductos.objects.filter(id_venta=venta)), Decimal('0'))
            venta.subtotal = total_serv + total_prod
            venta.save(update_fields=['subtotal'])
        venta = self.get_queryset().get(pk=pk)
        return Response(VentaSerializer(venta).data)

    @action(detail=False, methods=['post'], url_path='crear-ticket')
    def crear_ticket(self, request):
        if not Cajas.objects.filter(fecha_cierre__isnull=True).exists():
            return Response(
                {'detail': 'No hay una caja abierta.'},
                status=status.HTTP_409_CONFLICT,
            )

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

        telefono_raw = str(cliente_nuevo.get('telefono') or '').strip()
        tel = ''.join(ch for ch in telefono_raw if ch.isdigit())
        cliente = None
        if tel:
            candidatos = []
            for c in Clientes.objects.all().order_by('-id_cliente'):
                if ''.join(ch for ch in str(c.telefono or '') if ch.isdigit()) != tel:
                    continue
                exacto = str(c.telefono or '').strip() == telefono_raw
                candidatos.append((exacto, c))
            for exacto, c in candidatos:
                if exacto:
                    cliente = c
                    break
            if cliente is None and candidatos:
                cliente = candidatos[0][1]
        email = (cliente_nuevo.get('email') or '').strip() or None
        if cliente is None:
            cliente = Clientes.objects.create(
                telefono=cliente_nuevo['telefono'],
                nombre=cliente_nuevo['nombre'],
                apellido=cliente_nuevo['apellido'],
                email=email,
            )
        elif email and not cliente.email:
            cliente.email = email
            cliente.save(update_fields=['email'])
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

            if venta.anulada:
                return Response(
                    {'detail': 'La venta está anulada o cancelada.'},
                    status=status.HTTP_409_CONFLICT,
                )

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
