# cases/serializers.py
#
# WHY each change:
#
# 1. Import from .models now uses the inspectdb model names (Cases, CrimeTypes,
#    Locations, Suspects) instead of the old Django-managed names.
#
# 2. The old serializer had:
#      display_id = f'CR-2024-{obj.pk:04d}'
#    But pk is now a string like 'CR-2024-1001'. We expose it directly as 'id'.
#    No reformatting needed — the DB already stores the formatted ID.
#
# 3. The old serializer mapped 'victim' → model field 'victim'.
#    The DB column is 'victim_name', so we map correctly.
#
# 4. 'date' comes from 'date_filed' (a DateField), not created_at.
#
# 5. to_representation() reads from the real FK objects (crime_type.name,
#    suspect.name, location.name) — same pattern as before but with correct
#    model field names.
#
# 6. _resolve_fks uses get_or_create on the real table models.

from rest_framework import serializers
from .models import Cases, CrimeTypes, Locations, Suspects


# ── FK resolution helpers ─────────────────────────────────────────────────────

def _get_or_create_crime_type(name: str) -> CrimeTypes:
    obj, _ = CrimeTypes.objects.get_or_create(
        name__iexact=name,
        defaults={
            'name':      name,
            'color_hex': '#3b82f6',
            'icon':      'fa-tag',
            # created_at is NOT NULL in DB — provide a default
            'created_at': __import__('django.utils.timezone', fromlist=['now']).now(),
        }
    )
    return obj


def _get_or_create_location(name: str) -> Locations:
    try:
        return Locations.objects.get(name__iexact=name)
    except Locations.DoesNotExist:
        from django.utils import timezone
        return Locations.objects.create(
            name=name,
            city='Unknown',
            state='Unknown',
            latitude=0,
            longitude=0,
            created_at=timezone.now(),
        )


def _get_or_create_suspect(name: str) -> Suspects | None:
    if not name or name.strip().lower() in ('', 'unknown'):
        return None                         # DB allows NULL suspect FK
    from django.utils import timezone
    obj, _ = Suspects.objects.get_or_create(
        name__iexact=name.strip(),
        defaults={
            'name':          name.strip(),
            'is_absconding': 0,
            'created_at':    timezone.now(),
        }
    )
    return obj


# ── Main serializer ───────────────────────────────────────────────────────────

class CaseSerializer(serializers.ModelSerializer):
    """
    READ  → flat JSON matching frontend contract
    WRITE → accepts those same flat fields; resolves FKs in create/update.
    """
    
    # FIXED: Tell Django about our custom frontend fields so it doesn't crash
    # looking for them directly on the Cases database model.
    date     = serializers.CharField(required=False)
    type     = serializers.CharField(required=False)
    victim   = serializers.CharField(required=False)
    suspect  = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    location = serializers.CharField(required=False)
    desc     = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model  = Cases
        fields = ['id', 'date', 'type', 'victim', 'suspect', 'location', 'status', 'desc']

    # ── READ ──────────────────────────────────────────────────────────────────
    # ── READ ──────────────────────────────────────────────────────────────────

    def to_representation(self, instance):
        # FIXED: Check if date_filed is already a string, or if it needs isoformat()
        date_val = instance.date_filed
        if date_val:
            formatted_date = date_val.isoformat() if hasattr(date_val, 'isoformat') else str(date_val)
        else:
            formatted_date = None

        return {
            'id':       instance.id,
            'date':     formatted_date,  # Uses our safe formatted date
            'type':     instance.crime_type.name,
            'victim':   instance.victim_name,
            'suspect':  instance.suspect.name if getattr(instance, 'suspect', None) else 'Unknown',
            'location': instance.location.name,
            'status':   instance.status,
            'desc':     instance.description or '',
            
            # (If you kept the tracking fields from earlier, leave them here!)
            'reported_by': instance.reported_by.username if getattr(instance, 'reported_by', None) else 'System',
            'assigned_to': instance.assigned_to.full_name if getattr(instance, 'assigned_to', None) else 'Unassigned',
        }

    # ── WRITE ─────────────────────────────────────────────────────────────────

    def to_internal_value(self, data):
        """
        Accept the flat frontend payload. Strip read-only fields the UI may send.
        We validate just the required fields manually here and leave FK resolution
        to create()/update() so we don't need to teach DRF about custom field types.
        """
        mutable = data.copy() if hasattr(data, 'copy') else dict(data)
        mutable.pop('id', None)

        errors = {}
        if not mutable.get('victim'):
            errors['victim'] = ['This field is required.']
        if not mutable.get('type'):
            errors['type'] = ['This field is required.']
        if not mutable.get('location'):
            errors['location'] = ['This field is required.']
     
        if errors:
            raise serializers.ValidationError(errors)

        return mutable   # return as-is; _resolve_fks handles the rest

    def _resolve_fks(self, validated_data: dict) -> dict:
        out = dict(validated_data)

        # FIXED: Catch 'date' from frontend and rename it to 'date_filed' for the DB
        date_val = out.pop('date', None)
        if date_val:
            out['date_filed'] = date_val

        type_name = out.pop('type', None)
        if type_name:
            out['crime_type'] = _get_or_create_crime_type(type_name)

        # ... (keep the rest of the function exactly the same)

        loc_name = out.pop('location', None)
        if loc_name:
            out['location'] = _get_or_create_location(loc_name)

        suspect_name = out.pop('suspect', None)
        # Returns None for unknown/blank — FK is nullable in DB
        out['suspect'] = _get_or_create_suspect(suspect_name or '')

        desc = out.pop('desc', None)
        if desc is not None:
            out['description'] = desc

        # Map flat 'victim' → DB column name 'victim_name'
        victim = out.pop('victim', None)
        if victim is not None:
            out['victim_name'] = victim

        return out

    def create(self, validated_data):
        import uuid
        from django.utils import timezone
        data = self._resolve_fks(validated_data)

        # Generate the formatted ID if not provided
        # Pattern: CR-YYYY-NNNN derived from current year + a unique suffix
        if 'id' not in data:
            year = timezone.now().year
            # Use last 4 digits of a UUID integer for uniqueness
            suffix = str(uuid.uuid4().int)[-4:]
            data['id'] = f'CR-{year}-{suffix}'

        data.setdefault('created_at', timezone.now())
        data.setdefault('updated_at', timezone.now())
        data.setdefault('date_filed', timezone.now().date())

        return Cases.objects.create(**data)

    def update(self, instance, validated_data):
        from django.utils import timezone
        data = self._resolve_fks(validated_data)
        data['updated_at'] = timezone.now()
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance