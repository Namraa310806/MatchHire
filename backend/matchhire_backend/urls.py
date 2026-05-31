from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("backend.apps.users.urls")),
    path("api/jobs/", include("backend.apps.jobs.urls")),
    path("api/matching/", include("backend.apps.matching.urls")),
]
