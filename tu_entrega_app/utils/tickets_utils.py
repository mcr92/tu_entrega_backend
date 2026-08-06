from django.db.models import F, Value, FloatField,ExpressionWrapper
from django.db.models.functions import Cos, Sin, Radians, Cast, ACos
from tu_entrega_app.models import Messenger


def find_nearby_messengers(ticket_lat, ticket_lng, radius_km=5, number = 10):

    EARTH_RADIUS_KM = 6371.0

    lat1 = Radians(Cast(ticket_lat, FloatField()))
    lat2 = Radians(Cast(F('lat'), FloatField()))
    d_lng = Radians(Cast(ticket_lng, FloatField()) - Cast(F('lng'), FloatField()))

    distance_expression = ExpressionWrapper(
        EARTH_RADIUS_KM * ACos(
            Cos(lat1) * Cos(lat2) * Cos(d_lng) + Sin(lat1) * Sin(lat2)
        ),
        output_field=FloatField()
    )
    
    messengers = Messenger.objects.filter(
        is_active=True,
        lat__isnull=False,
        lng__isnull=False
    ).annotate(
        distance=distance_expression
    ).filter(
        distance__lte=radius_km
    ).order_by('distance')
    
    return messengers[:number]