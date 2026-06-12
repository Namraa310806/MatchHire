from django.urls import path

from .rbac_views import candidate_only_view, recruiter_only_view, verified_only_view

urlpatterns = [
    path("candidate-only/", candidate_only_view, name="rbac-candidate-only"),
    path("recruiter-only/", recruiter_only_view, name="rbac-recruiter-only"),
    path("verified-only/", verified_only_view, name="rbac-verified-only"),
]
