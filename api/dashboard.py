from datetime import datetime, time, timedelta
from decimal import Decimal
import unicodedata

from django.db.models.functions import Lower
from django.utils import timezone

from cajas.models import MovimientosCajas
from empleados.models import Empleados, LiquidacionesSemanales, RegistrosAsistencias
from turnos.models import Turnos, TurnosExpress
from ventas.models import Ventas


_ESTADOS_PENDIENTES = {'pendiente', 'pending'}
_ESTADOS_COMPLETADOS = {
    'finalizado',
    'completado',
    'realizado',
    'atendido',
    'asistio',
    'done',
    'finished',
    'completed',
}
_ESTADOS_AUSENTES = {
    'ausente',
    'ausencia',
    'falta',
    'faltas',
    'injustificado',
    'justificado',
    'no_presentado',
}


def _normalizar_estado(valor):
    texto = unicodedata.normalize('NFKD', str(valor or '').casefold())
    return ''.join(caracter for caracter in texto if not unicodedata.combining(caracter))


def _iso(fecha):
    return fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha)


def _total_movimientos(movimientos):
    total = sum(
        (
            Decimal(str(movimiento.get('total') or 0))
            for movimiento in movimientos
            if str(movimiento.get('tipo_movimiento') or '').strip().casefold()
            in {'cobro', 'ingreso'}
        ),
        Decimal('0'),
    )
    return f'{total:.2f}'


def _conteo_turnos(turnos):
    return {
        'total': len(turnos),
        'pendientes': sum(
            _normalizar_estado(turno.get('estado')) in _ESTADOS_PENDIENTES
            for turno in turnos
        ),
    }


def _contar_completados(turnos):
    return sum(
        _normalizar_estado(turno.get('estado')) in _ESTADOS_COMPLETADOS
        for turno in turnos
    )


def _construir_asistencia(barberos, asistencias, fecha):
    presentes = {
        asistencia.get('id_empleado_id')
        for asistencia in asistencias
        if _normalizar_estado(asistencia.get('estado')) not in _ESTADOS_AUSENTES
        and asistencia.get('id_empleado_id') is not None
    }
    lista = []
    for barbero in barberos:
        identificador = barbero.get('id_empleado')
        nombre = ' '.join(
            parte.strip()
            for parte in (barbero.get('nombre'), barbero.get('apellido'))
            if parte and parte.strip()
        )
        lista.append({
            'id': identificador,
            'nombre': nombre,
            'presente': identificador in presentes,
        })

    lista.sort(key=lambda barbero: barbero['nombre'].casefold())
    return {
        'fecha': _iso(fecha),
        'presentes': sum(barbero['presente'] for barbero in lista),
        'total': len(lista),
        'barberos': lista,
    }


def calcular_resumen_dashboard(
    *,
    fecha_hoy,
    fecha_caja,
    fecha_barberos,
    fecha_cortes,
    turnos_hoy,
    turnos_express_hoy,
    movimientos_caja_hoy,
    movimientos_caja_fecha,
    tickets_abiertos,
    liquidaciones_pendientes,
    barberos,
    asistencias,
    turnos_cortes,
    turnos_express_cortes,
):
    return {
        'turnos_hoy': _conteo_turnos([*turnos_hoy, *turnos_express_hoy]),
        'caja_hoy': _total_movimientos(movimientos_caja_hoy),
        'tickets_abiertos': tickets_abiertos,
        'liquidaciones_pendientes': liquidaciones_pendientes,
        'caja': {
            'fecha': _iso(fecha_caja),
            'ingresos': _total_movimientos(movimientos_caja_fecha),
        },
        'asistencia': _construir_asistencia(barberos, asistencias, fecha_barberos),
        'cortes': {
            'fecha': _iso(fecha_cortes),
            'realizados': _contar_completados([*turnos_cortes, *turnos_express_cortes]),
        },
        'fecha_hoy': _iso(fecha_hoy),
    }


def _rango_dia(fecha):
    inicio_local = datetime.combine(fecha, time.min)
    fin_local = inicio_local + timedelta(days=1)
    zona = timezone.get_current_timezone()
    return (
        timezone.make_aware(inicio_local, zona),
        timezone.make_aware(fin_local, zona),
    )


def _movimientos_caja(fecha):
    inicio, fin = _rango_dia(fecha)
    return list(
        MovimientosCajas.objects.annotate(
            tipo_normalizado=Lower('tipo_movimiento'),
        )
        .filter(
            fecha__gte=inicio,
            fecha__lt=fin,
            tipo_normalizado__in=('cobro', 'ingreso'),
        )
        .values('tipo_movimiento', 'total')
    )


def _turnos_del_dia(fecha):
    inicio, fin = _rango_dia(fecha)
    turnos = list(
        Turnos.objects.filter(fecha=fecha).values('estado', 'id_empleado_id')
    )
    turnos_express = list(
        TurnosExpress.objects.filter(
            fecha__gte=inicio,
            fecha__lt=fin,
        ).values('estado', 'id_empleado_id')
    )
    return turnos, turnos_express


def obtener_resumen_dashboard(
    *,
    fecha_hoy,
    fecha_caja,
    fecha_barberos,
    fecha_cortes,
):
    turnos_hoy, turnos_express_hoy = _turnos_del_dia(fecha_hoy)
    turnos_cortes, turnos_express_cortes = (
        (turnos_hoy, turnos_express_hoy)
        if fecha_cortes == fecha_hoy
        else _turnos_del_dia(fecha_cortes)
    )
    movimientos_hoy = _movimientos_caja(fecha_hoy)
    movimientos_fecha = (
        movimientos_hoy
        if fecha_caja == fecha_hoy
        else _movimientos_caja(fecha_caja)
    )

    inicio_asistencia, fin_asistencia = _rango_dia(fecha_barberos)
    barberos = list(
        Empleados.objects.filter(id_rol__nombre__iexact='Barbero')
        .values('id_empleado', 'nombre', 'apellido')
    )
    asistencias = list(
        RegistrosAsistencias.objects.filter(
            fecha__gte=inicio_asistencia,
            fecha__lt=fin_asistencia,
        ).values('id_empleado_id', 'estado')
    )

    return calcular_resumen_dashboard(
        fecha_hoy=fecha_hoy,
        fecha_caja=fecha_caja,
        fecha_barberos=fecha_barberos,
        fecha_cortes=fecha_cortes,
        turnos_hoy=turnos_hoy,
        turnos_express_hoy=turnos_express_hoy,
        movimientos_caja_hoy=movimientos_hoy,
        movimientos_caja_fecha=movimientos_fecha,
        tickets_abiertos=Ventas.objects.filter(estado=False).count(),
        liquidaciones_pendientes=LiquidacionesSemanales.objects.filter(
            estado=False,
        ).count(),
        barberos=barberos,
        asistencias=asistencias,
        turnos_cortes=turnos_cortes,
        turnos_express_cortes=turnos_express_cortes,
    )
