from django.urls import include, path

from .views import health_check


urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("auth/", include("apps.users.auth_urls")),
    path("users/", include("apps.users.urls")),
    path("jobs/", include("apps.jobs.urls")),
    path("matching/", include("apps.matching.urls")),
]
