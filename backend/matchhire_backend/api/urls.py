from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from .views import health_check, health_live, health_ready


urlpatterns = [
    # Schema and documentation endpoints
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
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
