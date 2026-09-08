# analytics/views.py
#
# WHY each change:
#
# 1. 'formatted_id' was f'CR-2024-{c.pk:04d}' — but pk is already 'CR-2024-1001'.
#    Now we just use c.id directly.
#
# 2. 'victim' → correct DB column is 'victim_name'.
#
# 3. analytics_yearly / analytics_monthly now group by 'date_filed' (a DateField)
#    not 'created_at' (a DateTimeField).  date_filed is the canonical "when the
#    crime occurred / was reported" field and matches what the seed data uses.
#
# 4. analytics_heatmap groups by location__name — unchanged but now uses Cases
#    (not Case) from the corrected models import.
#
# 5. Alert count uses is_active=1 (integer) not is_active=True.

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncYear

from cases.models import Cases
from alerts.models import Alerts

MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun',
               'Jul','Aug','Sep','Oct','Nov','Dec']


@api_view(['GET'])
@permission_classes([AllowAny])
def analytics_summary(request):
    """
    GET /api/analytics/summary/
    KPI cards + crime-type donut chart + recent 5 cases.
    """
    open_count   = Cases.objects.filter(status='Open').count()
    closed_count = Cases.objects.filter(status='Closed').count()
    inv_count    = Cases.objects.filter(status='Under Investigation').count()
    total        = open_count + closed_count + inv_count

    # Donut chart
    by_type = list(
        Cases.objects
        .values('crime_type__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    by_type_clean = [
        {'crime_type': row['crime_type__name'], 'count': row['count']}
        for row in by_type
    ]

    # Recent 5 cases — select_related avoids N+1
    recent = []
    for c in (
        Cases.objects
        .select_related('crime_type', 'suspect', 'location')
        .order_by('-created_at')[:5]
    ):
        recent.append({
            'formatted_id': c.id,                        # already 'CR-2024-1001'
            'victim':       c.victim_name,               # correct column name
            'crime_type':   c.crime_type.name,
            'status':       c.status,
            'date':         c.date_filed.isoformat() if c.date_filed else None,
        })

    return Response({
        'status_counts': {
            'open':          open_count,
            'closed':        closed_count,
            'investigation': inv_count,
        },
        'total_cases':   total,
        'active_alerts': Alerts.objects.filter(is_active=1).count(),  # integer, not bool
        'by_crime_type': by_type_clean,
        'recent_cases':  recent,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def analytics_yearly(request):
    """
    GET /api/analytics/yearly/
    Year-wise per-crime-type counts for the line chart.
    Groups by date_filed (the actual report date), not created_at.
    """
    rows = (
        Cases.objects
        .annotate(year=TruncYear('date_filed'))   # date_filed, not created_at
        .values('year', 'crime_type__name')
        .annotate(count=Count('id'))
        .order_by('year', 'crime_type__name')
    )

    data_map  = {}
    years_set = set()
    for row in rows:
        yr = row['year'].year
        ct = row['crime_type__name']
        years_set.add(yr)
        data_map.setdefault(ct, {})[yr] = row['count']

    years  = sorted(years_set)
    series = [
        {'crime_type': ct, 'data': [yr_map.get(yr, 0) for yr in years]}
        for ct, yr_map in sorted(data_map.items())
    ]
    return Response({'years': years, 'series': series})


@api_view(['GET'])
@permission_classes([AllowAny])
def analytics_monthly(request):
    """
    GET /api/analytics/monthly/?year=2024
    Monthly case counts for the bar chart.
    Groups by date_filed.
    """
    try:
        year = int(request.query_params.get('year', 2024))
    except ValueError:
        year = 2024

    rows = (
        Cases.objects
        .filter(date_filed__year=year)            # date_filed, not created_at
        .annotate(month=TruncMonth('date_filed'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    month_map = {row['month'].month: row['count'] for row in rows}

    return Response({
        'year':   year,
        'labels': MONTH_NAMES,
        'data':   [month_map.get(m, 0) for m in range(1, 13)],
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def analytics_heatmap(request):
    """
    GET /api/analytics/heatmap/
    Per-location incident counts.
    """
    rows = (
        Cases.objects
        .values('location__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    def heat_level(n):
        if n >= 70: return 'critical'
        if n >= 45: return 'high'
        if n >= 20: return 'medium'
        return 'low'

    return Response([
        {
            'name':  row['location__name'],
            'count': row['count'],
            'level': heat_level(row['count']),
        }
        for row in rows if row['location__name']
    ])