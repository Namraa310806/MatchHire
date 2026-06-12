from django.urls import path

from .views import (
    ResumeUploadView,
    ResumeListView,
    ResumeDetailView,
    ActiveResumeView,
    ResumeActivateView,
    ParseResumeView,
    ParsedResumeDetailView,
)

urlpatterns = [
    path("upload/", ResumeUploadView.as_view(), name="resume-upload"),
    path("", ResumeListView.as_view(), name="resume-list"),
    path("<uuid:id>/", ResumeDetailView.as_view(), name="resume-detail"),
    path("<uuid:id>/activate/", ResumeActivateView.as_view(), name="resume-activate"),
    path("<uuid:id>/parse/", ParseResumeView.as_view(), name="resume-parse"),
    path("<uuid:id>/parsed/", ParsedResumeDetailView.as_view(), name="resume-parsed"),
    path("active/", ActiveResumeView.as_view(), name="resume-active"),
]
