from django.urls import path

from .views import (
    JobCreateView,
    MyJobsListView,
    JobDetailView,
    JobCloseView,
    PublicJobListView,
)


urlpatterns = [
    path("", PublicJobListView.as_view(), name="job-public-list"),
    path("create/", JobCreateView.as_view(), name="job-create"),
    path("my/", MyJobsListView.as_view(), name="job-my-list"),
    path("<uuid:id>/", JobDetailView.as_view(), name="job-detail"),
    path("<uuid:id>/close/", JobCloseView.as_view(), name="job-close"),
]
