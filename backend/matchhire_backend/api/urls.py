from django.urls import include, path
from django.http import HttpResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from .views import health_check, health_live, health_ready, health_detailed, version_info


def metrics_view(request):
    """Prometheus metrics endpoint."""
    from matchhire_backend.core.metrics import get_metrics
    return HttpResponse(get_metrics(), content_type='text/plain')


urlpatterns = [
    # Schema and documentation endpoints
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Health and metrics endpoints
    path("health/", health_check),
    path("health/live", health_live),
    path("health/ready", health_ready),
    path("health/detailed", health_detailed),
    path("health/version", version_info),
    path("metrics/", metrics_view),
    # API endpoints
    path("auth/", include("apps.users.auth_urls")),
    path("profile/", include("apps.users.profile_urls")),
    path("users/", include("apps.users.urls")),
    path("jobs/", include("apps.jobs.urls")),
    path("matching/", include("apps.matching.urls")),
    path("resumes/", include("apps.resumes.urls")),
    path("applications/", include("apps.applications.urls")),
    path("", include("apps.interviews.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("admin/", include("apps.admin.urls")),
]
