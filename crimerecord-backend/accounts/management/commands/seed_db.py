"""
python manage.py seed_db

Seeds the Django DB from the data defined in database.sql:
  - CrimeType rows  (crime_types table)
  - Location rows   (locations table)
  - Suspect rows    (suspects table)
  - Alert rows      (alerts table)
  - Demo users      (citizen, officer, admin, officer2, citizen2)
    all with password: password123

Run ONCE after migrations. Safe to re-run — uses get_or_create throughout.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


CRIME_TYPES = [
    ('Theft',        '#3b82f6', 'fa-bag-shopping'),
    ('Robbery',      '#e8334a', 'fa-gun'),
    ('Assault',      '#f5732a', 'fa-hand-fist'),
    ('Fraud',        '#f0c040', 'fa-file-invoice-dollar'),
    ('Cybercrime',   '#22d3ee', 'fa-laptop-code'),
    ('Murder',       '#dc2626', 'fa-skull'),
    ('Kidnapping',   '#a855f7', 'fa-person-harassed'),
    ('Vandalism',    '#14b8a6', 'fa-spray-can'),
    ('Drug Offense', '#ec4899', 'fa-pills'),
]

LOCATIONS = [
    # (name, city, state, lat, lng, zone)
    ('Koramangala',    'Bengaluru', 'Karnataka', 12.934533, 77.626579, 'South'),
    ('MG Road',        'Bengaluru', 'Karnataka', 12.975190, 77.606900, 'Central'),
    ('Whitefield',     'Bengaluru', 'Karnataka', 12.969720, 77.749900, 'East'),
    ('Indiranagar',    'Bengaluru', 'Karnataka', 12.978300, 77.640800, 'Central'),
    ('Marathahalli',   'Bengaluru', 'Karnataka', 12.956900, 77.701000, 'East'),
    ('Electronic City','Bengaluru', 'Karnataka', 12.839400, 77.680200, 'South'),
    ('Hebbal',         'Bengaluru', 'Karnataka', 13.035100, 77.597300, 'North'),
    ('BTM Layout',     'Bengaluru', 'Karnataka', 12.916200, 77.610600, 'South'),
    ('Jayanagar',      'Bengaluru', 'Karnataka', 12.925100, 77.583500, 'South'),
    ('Banashankari',   'Bengaluru', 'Karnataka', 12.922600, 77.548300, 'South'),
    ('HSR Layout',     'Bengaluru', 'Karnataka', 12.911400, 77.644700, 'South'),
    ('Rajajinagar',    'Bengaluru', 'Karnataka', 12.990600, 77.551800, 'West'),
    ('Yelahanka',      'Bengaluru', 'Karnataka', 13.099700, 77.596400, 'North'),
    ('Malleshwaram',   'Bengaluru', 'Karnataka', 13.003100, 77.571500, 'West'),
    ('Sadashivanagar', 'Bengaluru', 'Karnataka', 13.009500, 77.583800, 'North'),
    ('Basavanagudi',   'Bengaluru', 'Karnataka', 12.941900, 77.573400, 'South'),
    ('Connaught Place','Delhi',     'Delhi',     28.632700, 77.219800, None),
    ('Andheri',        'Mumbai',    'Maharashtra', 19.119600, 72.846500, None),
    ('Banjara Hills',  'Hyderabad', 'Telangana', 17.410500, 78.448100, None),
    ('T. Nagar',       'Chennai',   'Tamil Nadu', 13.033900, 80.231900, None),
]

SUSPECTS = [
    # (name, alias, age, gender, is_absconding, notes)
    ('Ramesh Kumar',    'Ramu',       34, 'Male',    False, 'Previously convicted for robbery in 2019.'),
    ('Vijay S.',        None,         28, 'Male',    False, 'Identified via CCTV footage from pub vicinity.'),
    ('Ankit Sharma',    'Sharma Ji',  42, 'Male',    False, 'Has prior fraud cases in Pune and Bengaluru.'),
    ('Ganesh R.',       None,         25, 'Male',    False, 'Local resident. Released on bail.'),
    ('Ravi Gowda',      'Ravi Drugs', 33, 'Male',    False, 'History of narcotics offences.'),
    ('Suresh T.',       None,         38, 'Male',    False, 'Arrested. Child found safe within 6 hours.'),
    ('Dinesh M.',       None,         50, 'Male',    False, 'Investment scheme operator. Under custody.'),
    ('Nagaraju K.',     'Naga',       45, 'Male',    True,  'Absconding. Armed & dangerous.'),
    ('Mukesh T.',       None,         31, 'Male',    False, 'Domestic violence case. Bail granted.'),
    ('Sanjay V.',       None,         36, 'Male',    False, 'Fake job placement agent. Warrant issued.'),
    ('Unknown',         None,         None,'Unknown',False, 'Unidentified suspect.'),
    ('3 Unknown Males', None,         None,'Unknown',False, 'Three unidentified male suspects.'),
    ('Group of 5',      None,         None,'Unknown',False, 'Drug trafficking ring. Raids ongoing.'),
]

# (title, description, severity, alert_type, location_label)
ALERTS = [
    (
        'Armed Gang Activity — MG Road',
        'Three suspects armed with bladed weapons were reported near the commercial district. '
        'Public advised to avoid the area and report sightings to 100.',
        'critical', 'Incident Alert', 'MG Road',
    ),
    (
        'Acid Attack Survivor Update',
        'Victim Lakshmi Prasad (Case #CR-2024-1010) is in stable condition. '
        'Special investigation cell has taken over the case.',
        'critical', 'Case Update', 'Banashankari',
    ),
    (
        'Pickpocket Surge in Marathahalli',
        'A 40% increase in pickpocketing incidents near Marathahalli bridge. '
        'Plain-clothes officers deployed. Secure your valuables.',
        'warning', 'Public Advisory', 'Marathahalli',
    ),
    (
        'Online Banking Fraud Wave',
        'Bengaluru Cyber Crime unit recorded 14 new OTP-based banking fraud cases this week. '
        'Do NOT share OTPs over phone.',
        'warning', 'Cyber Alert', 'City-wide',
    ),
    (
        'Absconder Alert — Nagaraju K.',
        'Suspect in murder case #CR-2024-1014 remains at large. '
        'Last seen near Yelahanka. Call 1090 with information.',
        'warning', 'Wanted Alert', 'Yelahanka',
    ),
    (
        'Operation Clean Sweep — Drug Bust',
        'Simultaneous raids across 5 locations in Electronic City. '
        'Operation ongoing. Press briefing tomorrow at 11:00 AM.',
        'info', 'Operation Update', 'Electronic City',
    ),
    (
        'New CCTV Network Deployment',
        '158 new cameras installed across Koramangala and Indiranagar. Live from next week.',
        'info', 'Infrastructure', 'Koramangala / Indiranagar',
    ),
    (
        'Q2 Crime Statistics Released',
        'Total reported crimes dropped 12% vs Q1. Theft remains most common at 34%. '
        'Full report on official portal.',
        'info', 'Statistics', 'City-wide',
    ),
    (
        'Investment Fraud Ring Dismantled',
        'Ponzi scheme busted across Rajajinagar area. 8 arrested, ₹3.2 crore recovered. '
        'Victims: register at nearest station.',
        'critical', 'Arrest Made', 'Rajajinagar',
    ),
]

# Demo users: (username, password, is_staff, is_superuser)
DEMO_USERS = [
    ('citizen',  'password123', False, False),
    ('officer',  'password123', True,  False),
    ('admin',    'password123', True,  True),
    ('officer2', 'password123', True,  False),
    ('citizen2', 'password123', False, False),
]


class Command(BaseCommand):
    help = 'Seed DB with crime types, locations, suspects, alerts and demo users.'

    def handle(self, *args, **kwargs):
        from cases.models import CrimeType, Location, Suspect
        from alerts.models import Alert

        # ── CrimeTypes ────────────────────────────────────────────────────────
        self.stdout.write('Seeding crime types…')
        for name, color, icon in CRIME_TYPES:
            CrimeType.objects.get_or_create(
                name=name,
                defaults={'color_hex': color, 'icon': icon}
            )

        # ── Locations ─────────────────────────────────────────────────────────
        self.stdout.write('Seeding locations…')
        for name, city, state, lat, lng, zone in LOCATIONS:
            Location.objects.get_or_create(
                name=name,
                defaults={
                    'city': city, 'state': state,
                    'latitude': lat, 'longitude': lng,
                    'zone': zone,
                }
            )

        # ── Suspects ──────────────────────────────────────────────────────────
        self.stdout.write('Seeding suspects…')
        for name, alias, age, gender, absconding, notes in SUSPECTS:
            Suspect.objects.get_or_create(
                name=name,
                defaults={
                    'alias': alias or '',
                    'age': age,
                    'gender': gender,
                    'is_absconding': absconding,
                    'notes': notes,
                }
            )

        # ── Alerts ────────────────────────────────────────────────────────────
        self.stdout.write('Seeding alerts…')
        for title, desc, severity, atype, loc_label in ALERTS:
            Alert.objects.get_or_create(
                title=title,
                defaults={
                    'description':    desc,
                    'severity':       severity,
                    'alert_type':     atype,
                    'location_label': loc_label,
                    'is_active':      True,
                }
            )

        # ── Demo users ────────────────────────────────────────────────────────
        self.stdout.write('Seeding demo users…')
        for username, password, is_staff, is_super in DEMO_USERS:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    password=password,
                    is_staff=is_staff,
                    is_superuser=is_super,
                )
                self.stdout.write(f'  Created user: {username}')
            else:
                # Update password in case it was changed
                u = User.objects.get(username=username)
                u.set_password(password)
                u.is_staff      = is_staff
                u.is_superuser  = is_super
                u.save()
                self.stdout.write(f'  Updated user: {username}')

        self.stdout.write(self.style.SUCCESS(
            '\n✓ Seed complete.\n\n'
            'Demo login credentials (all use password: password123):\n'
            '  citizen  → role: CITIZEN  (can create cases)\n'
            '  citizen2 → role: CITIZEN\n'
            '  officer  → role: OFFICER  (full CRUD)\n'
            '  officer2 → role: OFFICER\n'
            '  admin    → role: OFFICER + Django admin access\n'
        ))