from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("matchhire_backend.api.urls")),
    path("api/", include("matchhire_backend.api.urls")),  # Backward compatibility
]
