from django.urls import path

from .auth_views import (
    BearerTokenObtainView,
    BearerTokenRefreshView,
    CookieLoginView,
    CookieTokenRefreshView,
    LogoutView,
    RegisterView,
)
from .github.views import GitHubConnectionView, GitHubSyncStatusView
from .resume.views import ResumeStatusView, ResumeUploadView
from .views import HealthCheckView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    # Authentication (Decision 8: cookie transport for browsers, Bearer for non-browser)
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", CookieLoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/token/", BearerTokenObtainView.as_view(), name="auth-token"),
    path("auth/token/refresh/", BearerTokenRefreshView.as_view(), name="auth-token-refresh"),
    path("auth/cookie/refresh/", CookieTokenRefreshView.as_view(), name="auth-cookie-refresh"),
    # Resume processing
    path("resumes/", ResumeUploadView.as_view(), name="resume-upload"),
    path(
        "resumes/status/<str:task_id>/",
        ResumeStatusView.as_view(),
        name="resume-status",
    ),
    # GitHub profile connection and sync
    path("profile/github/", GitHubConnectionView.as_view(), name="github-connection"),
    path(
        "profile/github/status/<str:task_id>/",
        GitHubSyncStatusView.as_view(),
        name="github-sync-status",
    ),
]
