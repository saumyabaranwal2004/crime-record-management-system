# cases/models.py
#
# WHY: The old models.py defined its own schema (auto_now_add, BooleanField,
# AUTH_USER_MODEL FKs). None of that matches the existing MySQL database.
# These models are generated from inspectdb output and set managed=False so
# Django never tries to CREATE/ALTER/DROP these tables.
#
# Rules followed:
#   - managed = False on every model
#   - db_table matches the real MySQL table name
#   - Field types match the actual MySQL column types exactly
#   - FKs point to the shared Users / Locations / Suspects / CrimeTypes tables
#   - No AUTH_USER_MODEL — the Users table is NOT Django's auth system

from django.db import models


class CrimeTypes(models.Model):
    # PK is auto-assigned by MySQL; inspectdb gives it an implicit id
    name       = models.CharField(unique=True, max_length=50)
    color_hex  = models.CharField(max_length=7)
    icon       = models.CharField(max_length=40)
    created_at = models.DateTimeField()

    class Meta:
        managed  = False
        db_table = 'crime_types'

    def __str__(self):
        return self.name


class Locations(models.Model):
    id        = models.SmallAutoField(primary_key=True)
    name      = models.CharField(unique=True, max_length=80)
    city      = models.CharField(max_length=60)
    state     = models.CharField(max_length=60)
    latitude  = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    zone      = models.CharField(max_length=7, blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed  = False
        db_table = 'locations'

    def __str__(self):
        return f'{self.name}, {self.city}'


class Suspects(models.Model):
    name          = models.CharField(max_length=100)
    alias         = models.CharField(max_length=100, blank=True, null=True)
    age           = models.PositiveIntegerField(blank=True, null=True)
    # DB column is VARCHAR(7): 'Male','Female','Other','Unknown'
    gender        = models.CharField(max_length=7, blank=True, null=True)
    nationality   = models.CharField(max_length=50, blank=True, null=True)
    # MySQL TINYINT(1) — Django IntegerField, not BooleanField, to avoid
    # Django trying to coerce the value; 0/1 works fine from MySQL
    is_absconding = models.IntegerField()
    photo_url     = models.CharField(max_length=255, blank=True, null=True)
    notes         = models.TextField(blank=True, null=True)
    created_at    = models.DateTimeField()

    class Meta:
        managed  = False
        db_table = 'suspects'

    def __str__(self):
        return self.name


class Users(models.Model):
    # WHY: This is NOT Django's auth User.  We use our own users table with
    # bcrypt hashes and a role column.  AUTH_USER_MODEL is removed from
    # settings so Django auth is not involved at all.
    username      = models.CharField(unique=True, max_length=40)
    password_hash = models.CharField(max_length=255)   # bcrypt hash
    role          = models.CharField(max_length=7)     # 'officer','admin','citizen'
    full_name     = models.CharField(max_length=100)
    badge_number  = models.CharField(max_length=20, blank=True, null=True)
    email         = models.CharField(max_length=120, blank=True, null=True)
    phone         = models.CharField(max_length=15, blank=True, null=True)
    is_active     = models.IntegerField()              # 0 / 1
    last_login    = models.DateTimeField(blank=True, null=True)
    created_at    = models.DateTimeField()

    class Meta:
        managed  = False
        db_table = 'users'

    def __str__(self):
        return self.username


class Cases(models.Model):
    # WHY: Primary key is a VARCHAR like 'CR-2024-1001' — already formatted by
    # the DB.  Old code had an integer PK and added 'CR-2024-' in Python; that
    # was double-formatting the ID and breaking lookups.
    id          = models.CharField(primary_key=True, max_length=20)
    date_filed  = models.DateField()
    crime_type  = models.ForeignKey(
        CrimeTypes, models.DO_NOTHING, db_column='crime_type_id'
    )
    victim_name = models.CharField(max_length=120)
    suspect     = models.ForeignKey(
        Suspects, models.DO_NOTHING,
        blank=True, null=True, db_column='suspect_id'
    )
    location    = models.ForeignKey(
        Locations, models.DO_NOTHING, db_column='location_id'
    )
    status      = models.CharField(max_length=19)
    description = models.TextField(blank=True, null=True)
    reported_by = models.ForeignKey(
        Users, models.DO_NOTHING, db_column='reported_by',
        blank=True, null=True, related_name='cases_reported'
    )
    assigned_to = models.ForeignKey(
        Users, models.DO_NOTHING, db_column='assigned_to',
        blank=True, null=True, related_name='cases_assigned'
    )
    created_at  = models.DateTimeField()
    updated_at  = models.DateTimeField()

    class Meta:
        managed  = False
        db_table = 'cases'

    def __str__(self):
        return f'{self.id} | {self.victim_name}'