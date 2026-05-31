from django.urls import path

from .auth_views import CandidateRegistrationView, LoginView, LogoutView, RefreshView, RecruiterRegistrationView


urlpatterns = [
	path("register/candidate/", CandidateRegistrationView.as_view(), name="auth-register-candidate"),
	path("register/recruiter/", RecruiterRegistrationView.as_view(), name="auth-register-recruiter"),
	path("login/", LoginView.as_view(), name="auth-login"),
	path("refresh/", RefreshView.as_view(), name="auth-refresh"),
	path("logout/", LogoutView.as_view(), name="auth-logout"),
]