from django.urls import path

from .views import CandidateMatchView, JobRecommendationsView, RecruiterCandidatesView


urlpatterns = [
    path("jobs/recommendations/", JobRecommendationsView.as_view(), name="job-recommendations"),
    path("recruiter/candidates/", RecruiterCandidatesView.as_view(), name="recruiter-candidates"),
]
