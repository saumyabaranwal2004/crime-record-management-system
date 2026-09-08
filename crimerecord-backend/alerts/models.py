# alerts/models.py
#
# WHY: The old alerts model had a denormalized 'location_label' CharField.
# That column does NOT exist in the actual DB.  The real schema has:
#   - location_id  FK → locations
#   - custom_loc   VARCHAR(120) — used when alert covers multiple areas
#
# We mirror the real schema exactly with managed=False.
# The serializer will COALESCE location.name and custom_loc into a single
# 'location_label' string for the frontend — that logic belongs in the
# serializer, not the model.
#
# severity column: DB is VARCHAR(8) — values: 'critical','warning','info'
# is_active column: DB is TINYINT(1) — we use IntegerField to match exactly

from django.db import models


class Alerts(models.Model):
    title       = models.CharField(max_length=200)
    description = models.TextField()
    severity    = models.CharField(max_length=8)    # 'critical'|'warning'|'info'
    alert_type  = models.CharField(max_length=60)
    location    = models.ForeignKey(
        'cases.Locations',              # shared table; point at the cases app model
        models.DO_NOTHING,
        db_column='location_id',
        blank=True, null=True
    )
    custom_loc  = models.CharField(
        max_length=120, blank=True, null=True,
        db_comment='Override if multi-area or city-wide'
    )
    is_active   = models.IntegerField()             # 0 / 1
    expires_at  = models.DateTimeField(blank=True, null=True)
    created_by  = models.ForeignKey(
        'cases.Users',
        models.DO_NOTHING,
        db_column='created_by',
        blank=True, null=True,
        related_name='alerts_created'
    )
    created_at  = models.DateTimeField()

    class Meta:
        managed  = False
        db_table = 'alerts'

    def __str__(self):
        return f'[{self.severity.upper()}] {self.title}'