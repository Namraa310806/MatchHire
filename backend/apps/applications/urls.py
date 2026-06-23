from django.urls import path
from .views import (
    JobApplyView,
    MyApplicationsListView,
    ApplicationDetailView,
    JobApplicationsListView,
)

app_name = "applications"

urlpatterns = [
    path("my/", MyApplicationsListView.as_view(), name="my-applications"),
    path("<uuid:id>/", ApplicationDetailView.as_view(), name="application-detail"),
]
