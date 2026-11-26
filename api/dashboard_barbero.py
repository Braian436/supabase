from datetime import datetime, time, timedelta
from decimal import Decimal
import unicodedata

from django.db.models import Q
from django.utils import timezone

from api.auth import empleado_de_usuario
from empleados.models import Empleados
from servicios.models import ServiciosTurnos
from turnos.models import Turnos, TurnosExpress
from turnos.api.horarios import hora_limite, momento_del_slot
from ventas.models import Ventas


_ESTADOS_PENDIENTES = {'pendiente', 'pending'}
_ESTADOS_FINALIZADOS = {
    'finalizado',
    'completado',
    'realizado',
    'atendido',
    'asistio',
    'done',
    'finished',
    'completed',
}


def _normalizar_estado(valor):
    texto = unicodedata.normalize('NFKD', str(valor or '').casefold())
    return ''.join(caracter for caracter in texto if not unicodedata.combining(caracter))


def _estado_de(turno):
    valor = turno.get('estado') if isinstance(turno, dict) else turno.estado
    return _normalizar_estado(valor)


def _hora_de(turno):
    return turno.get('hora') if isinstance(turno, dict) else turno.hora


def _es_vigente(turno, fecha, limite):
    """Los pendientes cuentan sólo si todavía pueden atenderse."""
    if _estado_de(turno) not in _ESTADOS_PENDIENTES:
        return True
    hora = _hora_de(turno)
    if hora is None:
        return False
    return momento_del_slot(fecha, hora) >= limite


def _rango_dia(fecha):
    inicio_local = datetime.combine(fecha, time.min)
    fin_local = inicio_local + timedelta(days=1)
    zona = timezone.get_current_timezone()
    return (
        timezone.make_aware(inicio_local, zona),
        timezone.make_aware(fin_local, zona),
    )


def _sumar_ventas(ventas):
    total = Decimal('0')
    for venta in ventas:
        subtotal = Decimal(str(venta.get('subtotal') or 0))
        descuento = Decimal(str(venta.get('descuento') or 0))
        total += subtotal - descuento
    return total


def _nombre_cliente(turno):
    cliente = turno.id_cliente
    if cliente is None:
        return 'Cliente'
    return f'{cliente.nombre} {cliente.apellido}'.strip()


def _servicios_de_turno(turno):
    nombres = [
        servicio.id_servicio.nombre
        for servicio in turno.servicios_turnos.all()
        if servicio.id_servicio_id
    ]
    return ', '.join(nombres) or 'Servicio'


def _serializar_turno(turno):
    return {
        'id': f'turno-{turno.pk}',
        'id_turno': turno.pk,
        'origen': 'turno',
        'fecha': turno.fecha.isoformat(),
        'hora': turno.hora.strftime('%H:%M'),
        'hora_fin': None,
        'cliente': _nombre_cliente(turno),
        'servicio': _servicios_de_turno(turno),
        'estado': _normalizar_estado(turno.estado),
    }


def _serializar_express(turno):
    return {
        'id': f'express-{turno.pk}',
        'id_turno': turno.pk,
        'origen': 'express',
        'fecha': turno.fecha.date().isoformat(),
        'hora': turno.hora.strftime('%H:%M'),
        'hora_fin': turno.hora_fin.strftime('%H:%M') if turno.hora_fin else None,
        'cliente': _nombre_cliente(turno),
        'servicio': turno.id_servicio.nombre if turno.id_servicio_id else 'Servicio',
        'estado': _normalizar_estado(turno.estado),
    }


def calcular_resumen_barbero(
    *,
    fecha,
    turnos_hoy,
    turnos_express_hoy,
    servicios_semana,
    ventas_semana,
    ventas_hoy,
    porcentaje_comision,
    proximos_turnos,
    ahora=None,
):
    total_semana = _sumar_ventas(ventas_semana)
    total_dia = _sumar_ventas(ventas_hoy)
    comision = (
        total_dia * Decimal(str(porcentaje_comision or 0)) / Decimal('100')
    ).quantize(Decimal('0.01'))
    limite = hora_limite(ahora)
    estados = [
        _estado_de(turno)
        for turno in [*turnos_hoy, *turnos_express_hoy]
        if _es_vigente(turno, fecha, limite)
    ]

    return {
        'fecha': fecha.isoformat(),
        'servicios_semana': servicios_semana,
        'total_semanal': f'{total_semana:.2f}',
        'comisiones_dia': f'{comision:.2f}',
        'turnos_hoy': len(estados),
        'turnos_hoy_pendientes': sum(
            estado in _ESTADOS_PENDIENTES for estado in estados
        ),
        'proximos_turnos': proximos_turnos,
    }


def _proximos_turnos(turnos_hoy, turnos_express_hoy, fecha, limite=None):
    if fecha < timezone.localdate():
        return []
    limite = limite or hora_limite()

    candidatos = []
    for turno in turnos_hoy:
        momento = momento_del_slot(fecha, turno.hora)
        if momento >= limite:
            candidatos.append((_serializar_turno(turno), momento))

    for turno in turnos_express_hoy:
        momento = momento_del_slot(fecha, turno.hora)
        if momento >= limite:
            candidatos.append((_serializar_express(turno), momento))

    candidatos.sort(key=lambda item: item[1])
    return [turno for turno, _ in candidatos[:3]]


def obtener_resumen_barbero(*, empleado, fecha, ahora=None):
    inicio, fin = _rango_dia(fecha)
    inicio_semana, _ = _rango_dia(fecha - timedelta(days=6))

    turnos_hoy = list(
        Turnos.objects.filter(id_empleado=empleado, fecha=fecha)
        .select_related('id_cliente')
        .prefetch_related('servicios_turnos__id_servicio')
        .order_by('hora')
    )
    turnos_express_hoy = list(
        TurnosExpress.objects.filter(
            id_empleado=empleado,
            fecha__gte=inicio,
            fecha__lt=fin,
        )
        .select_related('id_cliente', 'id_servicio')
        .order_by('hora')
    )

    turnos_semana = list(
        Turnos.objects.filter(
            id_empleado=empleado,
            fecha__gte=fecha - timedelta(days=6),
            fecha__lte=fecha,
        ).values('id_turno', 'estado')
    )
    ids_finalizados = [
        turno['id_turno']
        for turno in turnos_semana
        if _normalizar_estado(turno['estado']) in _ESTADOS_FINALIZADOS
    ]
    servicios_semana = (
        ServiciosTurnos.objects.filter(id_turno_id__in=ids_finalizados).count()
        if ids_finalizados
        else 0
    )
    if servicios_semana == 0:
        servicios_semana = len(ids_finalizados)

    express_semana = list(
        TurnosExpress.objects.filter(
            id_empleado=empleado,
            fecha__gte=inicio_semana,
            fecha__lt=fin,
        ).values('estado')
    )
    servicios_semana += sum(
        1
        for turno in express_semana
        if _normalizar_estado(turno['estado']) in _ESTADOS_FINALIZADOS
    )

    ventas_semana = list(
        Ventas.objects.filter(
            Q(id_turno__id_empleado=empleado)
            | Q(id_express__id_empleado=empleado),
            fecha_venta__gte=inicio_semana,
            fecha_venta__lt=fin,
            estado=True,
            anulada=False,
        ).values('subtotal', 'descuento', 'fecha_venta')
    )
    ventas_hoy = [
        venta
        for venta in ventas_semana
        if venta['fecha_venta']
        and timezone.localtime(venta['fecha_venta']).date() == fecha
    ]

    referencia = ahora if ahora is not None else timezone.localtime()
    limite = hora_limite(referencia)

    return calcular_resumen_barbero(
        fecha=fecha,
        turnos_hoy=turnos_hoy,
        turnos_express_hoy=turnos_express_hoy,
        servicios_semana=servicios_semana,
        ventas_semana=ventas_semana,
        ventas_hoy=ventas_hoy,
        porcentaje_comision=empleado.porcentaje_comision,
        proximos_turnos=_proximos_turnos(
            turnos_hoy, turnos_express_hoy, fecha, limite
        ),
        ahora=referencia,
    )


def resolver_empleado(usuario, empleado_id=None):
    """Resuelve el empleado a consultar respetando el rol del usuario."""
    propio = empleado_de_usuario(usuario)
    es_administrador = bool(
        usuario
        and usuario.is_authenticated
        and (
            usuario.is_superuser
            or usuario.groups.filter(name='Administrador').exists()
        )
    )

    if empleado_id is None:
        return propio

    if not es_administrador:
        if propio is None or propio.pk != empleado_id:
            return None
        return propio

    return Empleados.objects.filter(pk=empleado_id).first()
