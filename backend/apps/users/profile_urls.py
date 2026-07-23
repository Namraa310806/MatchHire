from django.urls import path

from .profile_views import CandidateProfileView, ProfileView, RecruiterProfileView


urlpatterns = [
    path("", ProfileView.as_view(), name="profile"),
    path("candidate/", CandidateProfileView.as_view(), name="profile-candidate"),
    path("recruiter/", RecruiterProfileView.as_view(), name="profile-recruiter"),
]
