from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginSerializer, UserSerializer
from .models import User


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


class LoginView(APIView):
	permission_classes = (AllowAny,)

	def post(self, request):
		serializer = LoginSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		email = serializer.validated_data["email"]
		password = serializer.validated_data["password"]
		user = User.objects.filter(email=email).first()
		if user is not None and not user.is_active:
			return Response({"message": "User account is inactive"}, status=status.HTTP_401_UNAUTHORIZED)

		user = authenticate(
			request=request,
			email=email,
			password=password,
		)
		if user is None:
			return Response({"message": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

		refresh = RefreshToken.for_user(user)
		response = Response(
			{"message": "Login successful", "user": UserSerializer(user).data},
			status=status.HTTP_200_OK,
		)
		_set_auth_cookies(response, str(refresh.access_token), str(refresh))
		return response


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