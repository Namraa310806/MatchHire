from django.contrib import admin
from django.urls import include, path
from django.conf import settings

from .api.views import health_check, health_live, health_ready, version_info


urlpatterns = [
    # Health endpoints (outside API versioning for orchestration systems)
    path("health/", health_check, name="health-check"),
    path("health/live/", health_live, name="health-live"),
    path("health/ready/", health_ready, name="health-ready"),
    # Version endpoint
    path("version/", version_info, name="version-info"),
    # Admin
    path("admin/", admin.site.urls, name="django-admin"),
    # API endpoints
    path("api/v1/", include("matchhire_backend.api.urls")),
    path("api/", include("matchhire_backend.api.urls")),  # Backward compatibility
]

# Django Debug Toolbar (only in development)
if settings.DEBUG:
    import debug_toolbar

    urlpatterns.insert(0, path("__debug__/", include(debug_toolbar.urls)))
