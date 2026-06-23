from django.urls import path

from .views import (
    JobCreateView,
    MyJobsListView,
    JobDetailView,
    JobCloseView,
    PublicJobListView,
)
from apps.applications.views import JobApplyView, JobApplicationsListView


urlpatterns = [
    path("", PublicJobListView.as_view(), name="job-public-list"),
    path("create/", JobCreateView.as_view(), name="job-create"),
    path("my/", MyJobsListView.as_view(), name="job-my-list"),
    path("<uuid:id>/", JobDetailView.as_view(), name="job-detail"),
    path("<uuid:id>/close/", JobCloseView.as_view(), name="job-close"),
    path("<uuid:job_id>/apply/", JobApplyView.as_view(), name="job-apply"),
    path("<uuid:job_id>/applications/", JobApplicationsListView.as_view(), name="job-applications"),
]
