from django.urls import path

from .views import (
    RecruiterDashboardView,
    CandidateDashboardView,
    JobAnalyticsView,
    TopCandidatesView,
)


urlpatterns = [
    path("recruiter/dashboard/", RecruiterDashboardView.as_view(), name="recruiter-dashboard"),
    path("candidate/dashboard/", CandidateDashboardView.as_view(), name="candidate-dashboard"),
    path("recruiter/jobs/<uuid:job_id>/", JobAnalyticsView.as_view(), name="job-analytics"),
    path("recruiter/jobs/<uuid:job_id>/top-candidates/", TopCandidatesView.as_view(), name="top-candidates"),
]
