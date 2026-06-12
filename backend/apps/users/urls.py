from django.urls import include, path


urlpatterns = [
	path("auth/", include("apps.users.auth_urls")),
	path("profile/", include("apps.users.profile_urls")),
	path("rbac/", include("apps.users.rbac_urls")),
]
