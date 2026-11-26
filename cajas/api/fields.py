import datetime

from django.utils import timezone as django_timezone
from rest_framework import serializers


class UTCDateTimeField(serializers.DateTimeField):
    """Serializa datetimes naive como si fueran UTC.

    Las tablas usan `timestamp without time zone` y guardan valores en UTC.
    DRF, al recibir un datetime naive, lo interpretaría en `settings.TIME_ZONE`
    (America/Argentina/Salta) y desplazaría la hora 3 horas. Este campo lo
    marca como UTC para que la API devuelva la hora argentina correcta.
    """

    def to_representation(self, value):
        if value is not None and django_timezone.is_naive(value):
            value = django_timezone.make_aware(value, datetime.timezone.utc)
        return super().to_representation(value)
