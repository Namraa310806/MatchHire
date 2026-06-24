from django.urls import path
from .views import (
    ApplicationInterviewsListView,
    InterviewDetailView,
    InterviewStatusUpdateView,
    InterviewHistoryView,
)

urlpatterns = [
    path(
        "applications/<uuid:application_id>/interviews/",
        ApplicationInterviewsListView.as_view(),
        name="application-interviews",
    ),
    path(
        "interviews/<uuid:interview_id>/",
        InterviewDetailView.as_view(),
        name="interview-detail",
    ),
    path(
        "interviews/<uuid:interview_id>/status/",
        InterviewStatusUpdateView.as_view(),
        name="interview-status-update",
    ),
    path(
        "interviews/<uuid:interview_id>/history/",
        InterviewHistoryView.as_view(),
        name="interview-history",
    ),
]
