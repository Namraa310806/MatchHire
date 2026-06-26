from django.urls import path

from .views import (
    AdminApplicationListView,
    AdminDashboardView,
    AdminJobDetailView,
    AdminJobListView,
    AdminResumeDetailView,
    AdminResumeListView,
    AdminUserDetailView,
    AdminUserListView,
)

app_name = "admin_moderation"

urlpatterns = [
    path("users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("users/<uuid:id>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("jobs/", AdminJobListView.as_view(), name="admin-job-list"),
    path("jobs/<uuid:id>/", AdminJobDetailView.as_view(), name="admin-job-detail"),
    path("resumes/", AdminResumeListView.as_view(), name="admin-resume-list"),
    path("resumes/<uuid:id>/", AdminResumeDetailView.as_view(), name="admin-resume-detail"),
    path("applications/", AdminApplicationListView.as_view(), name="admin-application-list"),
    path("dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
]
