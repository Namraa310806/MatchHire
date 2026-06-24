from django.urls import path
from .views import (
    JobApplyView,
    MyApplicationsListView,
    ApplicationDetailView,
    JobApplicationsListView,
    ApplicationStatusUpdateView,
    ApplicationHistoryView,
)

app_name = "applications"

urlpatterns = [
    path("my/", MyApplicationsListView.as_view(), name="my-applications"),
    path("<uuid:id>/", ApplicationDetailView.as_view(), name="application-detail"),
    path("<uuid:id>/status/", ApplicationStatusUpdateView.as_view(), name="application-status-update"),
    path("<uuid:id>/history/", ApplicationHistoryView.as_view(), name="application-history"),
]
