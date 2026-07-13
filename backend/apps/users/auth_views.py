from django.conf import settings
from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

from .serializers import (
	CandidateRegistrationSerializer,
	CurrentUserSerializer,
	LoginSerializer,
	ProfileNotFound,
	RecruiterRegistrationSerializer,
	UserSerializer,
)
from .models import User
from matchhire_backend.core.security_audit import SecurityAuditService


def _cookie_max_age(token_lifetime):
	return int(token_lifetime.total_seconds())


def _set_auth_cookies(response, access_token, refresh_token):
	response.set_cookie(
		settings.JWT_ACCESS_COOKIE_NAME,
		access_token,
		httponly=True,
		secure=settings.JWT_COOKIE_SECURE,
		samesite=settings.JWT_COOKIE_SAMESITE,
		path="/",
		max_age=_cookie_max_age(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]),
	)
	response.set_cookie(
		settings.JWT_REFRESH_COOKIE_NAME,
		refresh_token,
		httponly=True,
		secure=settings.JWT_COOKIE_SECURE,
		samesite=settings.JWT_COOKIE_SAMESITE,
		path="/",
		max_age=_cookie_max_age(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]),
	)


def _clear_auth_cookies(response):
	response.delete_cookie(settings.JWT_ACCESS_COOKIE_NAME, path="/")
	response.delete_cookie(settings.JWT_REFRESH_COOKIE_NAME, path="/")


def _build_authenticated_response(user, message, status_code=status.HTTP_200_OK):
	refresh = RefreshToken.for_user(user)
	response = Response(
		{"message": message, "user": UserSerializer(user).data},
		status=status_code,
	)
	_set_auth_cookies(response, str(refresh.access_token), str(refresh))
	return response


@extend_schema(
	tags=["Authentication"],
	summary="User login",
	description="Authenticate user with email and password. Returns JWT tokens in HTTP-only cookies.",
	request={
		"application/json": {
			"type": "object",
			"properties": {
				"email": {"type": "string", "format": "email"},
				"password": {"type": "string", "format": "password"}
			},
			"required": ["email", "password"]
		}
	},
	responses={
		200: OpenApiResponse(
			description="Login successful. JWT tokens set in HTTP-only cookies.",
			response={
				"type": "object",
				"properties": {
					"message": {"type": "string"},
					"user": {"type": "object", "properties": {"id": {"type": "string"}, "email": {"type": "string"}, "role": {"type": "string"}}}
				}
			}
		),
		401: OpenApiResponse(description="Invalid credentials or inactive account")
	},
	examples=[
		OpenApiExample(
			"Successful login",
			value={"email": "candidate@example.com", "password": "securepassword123"},
			response_only=False,
		),
	]
)
class LoginView(APIView):
	permission_classes = (AllowAny,)
	throttle_scope = 'login'

	def post(self, request):
		serializer = LoginSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		email = serializer.validated_data["email"]
		password = serializer.validated_data["password"]
		user = User.objects.filter(email=email).first()
		if user is not None and not user.is_active:
			SecurityAuditService.log_failed_login(email, self.get_client_ip(request))
			return Response({"message": "User account is inactive"}, status=status.HTTP_401_UNAUTHORIZED)

		user = authenticate(
			request=request,
			email=email,
			password=password,
		)
		if user is None:
			SecurityAuditService.log_failed_login(email, self.get_client_ip(request))
			return Response({"message": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

		return _build_authenticated_response(user, "Login successful")

	def get_client_ip(self, request):
		"""Get client IP address from request"""
		x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
		if x_forwarded_for:
			ip = x_forwarded_for.split(',')[0]
		else:
			ip = request.META.get('REMOTE_ADDR')
		return ip


@extend_schema(
	tags=["Authentication"],
	summary="Candidate registration",
	description="Register a new candidate account. Creates user and candidate profile. Returns JWT tokens in HTTP-only cookies.",
	request={
		"application/json": {
			"type": "object",
			"properties": {
				"email": {"type": "string", "format": "email"},
				"password": {"type": "string", "minLength": 8},
				"full_name": {"type": "string"}
			},
			"required": ["email", "password", "full_name"]
		}
	},
	responses={
		201: OpenApiResponse(description="Registration successful. JWT tokens set in HTTP-only cookies."),
		400: OpenApiResponse(description="Invalid input data")
	},
	examples=[
		OpenApiExample(
			"Candidate registration",
			value={"email": "candidate@example.com", "password": "securepassword123", "full_name": "John Doe"},
			response_only=False,
		),
	]
)
class CandidateRegistrationView(APIView):
	permission_classes = (AllowAny,)
	throttle_scope = 'registration'

	def post(self, request):
		serializer = CandidateRegistrationSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		with transaction.atomic():
			user = serializer.save()
		return _build_authenticated_response(user, "Registration successful", status.HTTP_201_CREATED)


@extend_schema(
	tags=["Authentication"],
	summary="Recruiter registration",
	description="Register a new recruiter account. Creates user and recruiter profile. Returns JWT tokens in HTTP-only cookies.",
	request={
		"application/json": {
			"type": "object",
			"properties": {
				"email": {"type": "string", "format": "email"},
				"password": {"type": "string", "minLength": 8},
				"full_name": {"type": "string"},
				"company_name": {"type": "string"}
			},
			"required": ["email", "password", "full_name", "company_name"]
		}
	},
	responses={
		201: OpenApiResponse(description="Registration successful. JWT tokens set in HTTP-only cookies."),
		400: OpenApiResponse(description="Invalid input data")
	},
	examples=[
		OpenApiExample(
			"Recruiter registration",
			value={"email": "recruiter@company.com", "password": "securepassword123", "full_name": "Jane Smith", "company_name": "Tech Corp"},
			response_only=False,
		),
	]
)
class RecruiterRegistrationView(APIView):
	permission_classes = (AllowAny,)
	throttle_scope = 'registration'

	def post(self, request):
		serializer = RecruiterRegistrationSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		with transaction.atomic():
			user = serializer.save()
		return _build_authenticated_response(user, "Registration successful", status.HTTP_201_CREATED)


@extend_schema(
	tags=["Authentication"],
	summary="Refresh access token",
	description="Refresh JWT access token using refresh token from HTTP-only cookie.",
	responses={
		200: OpenApiResponse(description="Token refreshed successfully. New access token set in cookie."),
		401: OpenApiResponse(description="Refresh token missing or invalid")
	}
)
class RefreshView(APIView):
	permission_classes = (AllowAny,)

	def post(self, request):
		refresh_token = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
		if not refresh_token:
			return Response({"message": "Refresh token is required"}, status=status.HTTP_401_UNAUTHORIZED)

		serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
		serializer.is_valid(raise_exception=True)

		response = Response({"message": "Token refreshed"}, status=status.HTTP_200_OK)
		_set_auth_cookies(
			response,
			serializer.validated_data["access"],
			serializer.validated_data.get("refresh", refresh_token),
		)
		return response


@extend_schema(
	tags=["Authentication"],
	summary="User logout",
	description="Logout user by blacklisting refresh token and clearing HTTP-only cookies.",
	responses={
		200: OpenApiResponse(description="Logout successful. Cookies cleared.")
	}
)
class LogoutView(APIView):
	permission_classes = (AllowAny,)

	def post(self, request):
		refresh_token = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
		if refresh_token:
			try:
				RefreshToken(refresh_token).blacklist()
			except Exception:
				pass

		response = Response({"message": "Logged out"}, status=status.HTTP_200_OK)
		_clear_auth_cookies(response)
		return response


@extend_schema(
	tags=["Users"],
	summary="Get current user",
	description="Retrieve information about the currently authenticated user.",
	responses={
		200: OpenApiResponse(description="User information retrieved successfully."),
		500: OpenApiResponse(description="Profile not found")
	}
)
class CurrentUserView(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		try:
			serializer = CurrentUserSerializer(request.user)
			return Response(serializer.data, status=status.HTTP_200_OK)
		except ProfileNotFound:
			return Response({"error": "Profile not found"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)