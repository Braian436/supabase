from datetime import datetime, timedelta

from django.utils import timezone


MARGEN_RESERVA_MINUTOS = 5


def es_dia_habil(fecha):
    """Los domingos están cerrados."""
    return fecha.weekday() != 6


def momento_del_slot(fecha, hora):
    """Devuelve el momento aware de un slot en la zona horaria configurada."""
    zona = timezone.get_current_timezone()
    momento = hora if isinstance(hora, datetime) else datetime.combine(fecha, hora)
    if timezone.is_naive(momento):
        return timezone.make_aware(momento, zona)
    return momento.astimezone(zona)


def hora_limite(ahora=None):
    """Momento mínimo para reservar: ahora más el margen de seguridad."""
    referencia = ahora if ahora is not None else timezone.localtime()
    if timezone.is_naive(referencia):
        referencia = timezone.make_aware(
            referencia, timezone.get_current_timezone()
        )
    return referencia + timedelta(minutes=MARGEN_RESERVA_MINUTOS)


def es_reservable(fecha, hora, ahora=None):
    return momento_del_slot(fecha, hora) >= hora_limite(ahora)
