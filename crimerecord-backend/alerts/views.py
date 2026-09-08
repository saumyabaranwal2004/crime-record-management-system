# alerts/views.py
#
# WHY: The old view filtered with is_active=True (Python bool).
# The DB column is TINYINT(1), so Django's mysql backend stores 0/1.
# Filtering with is_active=1 is explicit and always correct.
#
# select_related('location') prevents an N+1 query when the serializer
# calls obj.location.name for each alert row.

from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Alerts
from .serializers import AlertSerializer


class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/alerts/                all active alerts (public)
    GET /api/alerts/?severity=X     filter: critical | warning | info
    GET /api/alerts/<id>/           single alert detail
    """
    serializer_class   = AlertSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = (
            Alerts.objects
            .select_related('location')         # avoid N+1 on location_label
            .filter(is_active=1)
        )

        severity = self.request.query_params.get('severity')
        if severity and severity != 'all':
            qs = qs.filter(severity=severity)

        # Match the old model's ordering: critical first, then newest first
        return qs.order_by(
            # Use a CASE expression via conditional annotation
            # Django 4.2+ supports this cleanly with Case/When
            _severity_order(),
            '-created_at',
        )


def _severity_order():
    """Return a Case expression that maps severity → sort integer."""
    from django.db.models import Case, When, IntegerField
    return Case(
        When(severity='critical', then=0),
        When(severity='warning',  then=1),
        When(severity='info',     then=2),
        default=3,
        output_field=IntegerField(),
    )