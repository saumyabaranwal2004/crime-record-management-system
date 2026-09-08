from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    

    # Accounts: /api/me/  and  /api/register/
    path('api/', include('accounts.urls')),

    # Core APIs
    path('api/', include('cases.urls')),
    path('api/', include('alerts.urls')),
    path('api/', include('analytics.urls')),
]