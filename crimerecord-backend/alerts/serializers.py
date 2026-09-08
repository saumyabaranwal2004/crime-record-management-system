# alerts/serializers.py
#
# WHY: The frontend reads a.location_label — a single string.
# The DB has two columns: location_id (FK → locations.name) and custom_loc.
# We synthesize location_label in a SerializerMethodField using COALESCE logic:
#   1. If custom_loc is set → use it (multi-area / city-wide alerts)
#   2. Else if location FK is set → use location.name
#   3. Else → empty string
#
# is_active is stored as 0/1 in MySQL TINYINT.  We expose it as a boolean
# to the frontend (truthy/falsy behaviour is the same; explicit bool is cleaner).

from rest_framework import serializers
from .models import Alerts


class AlertSerializer(serializers.ModelSerializer):
    # Synthesize the flat string the frontend expects
    location_label = serializers.SerializerMethodField()
    is_active      = serializers.SerializerMethodField()

    class Meta:
        model  = Alerts
        fields = [
            'id', 'title', 'description', 'severity',
            'alert_type', 'location_label', 'is_active', 'created_at',
        ]

    def get_location_label(self, obj) -> str:
        # custom_loc takes precedence (city-wide / multi-area alerts)
        if obj.custom_loc:
            return obj.custom_loc
        # Fall back to the related location's name
        if obj.location_id and obj.location:
            return obj.location.name
        return ''

    def get_is_active(self, obj) -> bool:
        return bool(obj.is_active)