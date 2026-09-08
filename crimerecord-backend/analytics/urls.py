from django.urls import path
from .views import (
    analytics_summary,
    analytics_yearly,
    analytics_monthly,
    analytics_heatmap,
)

urlpatterns = [
    path('analytics/summary/', analytics_summary, name='analytics-summary'),
    path('analytics/yearly/',  analytics_yearly,  name='analytics-yearly'),
    path('analytics/monthly/', analytics_monthly, name='analytics-monthly'),
    path('analytics/heatmap/', analytics_heatmap, name='analytics-heatmap'),
]