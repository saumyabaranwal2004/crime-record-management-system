# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Alerts(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=8)
    alert_type = models.CharField(max_length=60)
    location = models.ForeignKey('Locations', models.DO_NOTHING, blank=True, null=True)
    custom_loc = models.CharField(max_length=120, blank=True, null=True, db_comment='Override if multi-area or city-wide')
    is_active = models.IntegerField()
    expires_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey('Users', models.DO_NOTHING, db_column='created_by', blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'alerts'


class CaseAuditLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    case_id = models.CharField(max_length=20)
    action = models.CharField(max_length=6)
    changed_by = models.PositiveIntegerField(blank=True, null=True)
    old_status = models.CharField(max_length=30, blank=True, null=True)
    new_status = models.CharField(max_length=30, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'case_audit_log'


class Cases(models.Model):
    id = models.CharField(primary_key=True, max_length=20, db_comment='e.g. CR-2024-1001')
    date_filed = models.DateField()
    crime_type = models.ForeignKey('CrimeTypes', models.DO_NOTHING)
    victim_name = models.CharField(max_length=120)
    suspect = models.ForeignKey('Suspects', models.DO_NOTHING, blank=True, null=True, db_comment='NULL = unknown')
    location = models.ForeignKey('Locations', models.DO_NOTHING)
    status = models.CharField(max_length=19)
    description = models.TextField(blank=True, null=True)
    reported_by = models.ForeignKey('Users', models.DO_NOTHING, db_column='reported_by', blank=True, null=True, db_comment='FK → users.id')
    assigned_to = models.ForeignKey('Users', models.DO_NOTHING, db_column='assigned_to', related_name='cases_assigned_to_set', blank=True, null=True, db_comment='FK → users.id (officer)')
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'cases'


class CrimeTypes(models.Model):
    name = models.CharField(unique=True, max_length=50)
    color_hex = models.CharField(max_length=7, db_comment='Chart colour')
    icon = models.CharField(max_length=40, db_comment='Font Awesome class')
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'crime_types'


class LocationCrimeStats(models.Model):
    pk = models.CompositePrimaryKey('location_id', 'stat_year')
    location = models.ForeignKey('Locations', models.DO_NOTHING)
    stat_year = models.TextField()  # This field type is a guess.
    total_cases = models.PositiveSmallIntegerField()
    heat_level = models.CharField(max_length=8)

    class Meta:
        managed = False
        db_table = 'location_crime_stats'


class Locations(models.Model):
    id = models.SmallAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=80)
    city = models.CharField(max_length=60)
    state = models.CharField(max_length=60)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    zone = models.CharField(max_length=7, blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'locations'


class MonthlyCrimeStats(models.Model):
    id = models.SmallAutoField(primary_key=True)
    stat_year = models.TextField()  # This field type is a guess.
    stat_month = models.PositiveIntegerField(db_comment='1=Jan … 12=Dec')
    total_cases = models.PositiveSmallIntegerField()

    class Meta:
        managed = False
        db_table = 'monthly_crime_stats'
        unique_together = (('stat_year', 'stat_month'),)


class Suspects(models.Model):
    name = models.CharField(max_length=100)
    alias = models.CharField(max_length=100, blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    gender = models.CharField(max_length=7, blank=True, null=True)
    nationality = models.CharField(max_length=50, blank=True, null=True)
    is_absconding = models.IntegerField()
    photo_url = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'suspects'


class Users(models.Model):
    username = models.CharField(unique=True, max_length=40)
    password_hash = models.CharField(max_length=255, db_comment='bcrypt hash')
    role = models.CharField(max_length=7)
    full_name = models.CharField(max_length=100)
    badge_number = models.CharField(max_length=20, blank=True, null=True, db_comment='Officers only')
    email = models.CharField(max_length=120, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    is_active = models.IntegerField()
    last_login = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'users'


class YearlyCrimeStats(models.Model):
    id = models.SmallAutoField(primary_key=True)
    stat_year = models.TextField()  # This field type is a guess.
    crime_type = models.ForeignKey(CrimeTypes, models.DO_NOTHING)
    total_cases = models.PositiveSmallIntegerField()

    class Meta:
        managed = False
        db_table = 'yearly_crime_stats'
        unique_together = (('stat_year', 'crime_type'),)
