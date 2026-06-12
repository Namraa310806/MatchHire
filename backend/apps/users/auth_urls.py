from django.urls import path

from .auth_views import (
	CandidateRegistrationView,
	CurrentUserView,
	LoginView,
	LogoutView,
	RefreshView,
	RecruiterRegistrationView,
)


urlpatterns = [
	path("register/candidate/", CandidateRegistrationView.as_view(), name="auth-register-candidate"),
	path("register/recruiter/", RecruiterRegistrationView.as_view(), name="auth-register-recruiter"),
	path("login/", LoginView.as_view(), name="auth-login"),
	path("refresh/", RefreshView.as_view(), name="auth-refresh"),
	path("logout/", LogoutView.as_view(), name="auth-logout"),
	path("me/", CurrentUserView.as_view(), name="auth-me"),
]