import logging

from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import mixins, viewsets
from rest_framework.renderers import JSONRenderer

from .serializers import FoodSerializer
from .models import Food

logger = logging.getLogger(__name__)


class FoodsView(mixins.ListModelMixin,
                mixins.CreateModelMixin,
                viewsets.GenericViewSet):
    """Read the approved catalog, or submit a new food for approval.

    Deliberately not a ModelViewSet: the client only ever lists and creates, so
    the detail routes (retrieve/update/destroy) are not generated at all. They
    previously existed, were unauthenticated, and returned 500 only because
    `queryset` was undefined.
    """

    serializer_class = FoodSerializer
    queryset = Food.objects.filter(approved=True)

    def list(self, request, *args, **kwargs):
        logger.info("Catalog request from %s", get_client_ip(request))

        # Generated before the query, not after. A food saved mid-request is
        # then included in the *next* response too (harmless duplicate the
        # client merges) rather than being skipped forever.
        now = timezone.now()

        approved = Food.objects.filter(approved=True)
        total = approved.count()

        raw_time = request.GET.get('time', None)
        since = parse_datetime(raw_time) if raw_time else None
        if raw_time and since is None:
            # A corrupt stored timestamp used to reach the ORM as None and 500.
            # Serving the full catalog instead lets the client heal itself.
            logger.warning("Unparseable ?time=%r; serving full catalog", raw_time)

        if since is None:
            foods = approved.order_by('-modified')
        else:
            foods = approved.filter(modified__gt=since).order_by('-modified')

        payload = FoodSerializer(foods, many=True).data

        # reset means "replace your whole global catalog with this payload".
        # Only true when the payload IS the whole catalog, and never when it is
        # empty -- an empty catalog previously satisfied 0 == 0 and ordered
        # every client to wipe itself with nothing to repopulate from.
        reset = total > 0 and len(payload) == total

        res = {
            "foods": payload,
            "timestamp": now,
            "reset": reset,
        }
        return HttpResponse(JSONRenderer().render(res),
                            content_type="application/json")


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
