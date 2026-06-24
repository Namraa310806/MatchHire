from django.urls import include, path

from .views import health_check


urlpatterns = [
    path("health/", health_check, name="health-check"),
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
]
