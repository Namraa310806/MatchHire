from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import CandidateProfile, RecruiterProfile
from .permissions import IsCandidate, IsRecruiter
from .serializers import (
	CandidateProfileSerializer,
	CandidateProfileUpdateSerializer,
	CurrentUserSerializer,
	ProfileNotFound,
	RecruiterProfileSerializer,
	RecruiterProfileUpdateSerializer,
	UserProfileUpdateSerializer,
)


@extend_schema(
	tags=["Profiles"],
	summary="Get user profile",
	description="Retrieve the current user's profile information. Authentication required.",
	responses={
		200: OpenApiResponse(description="Profile retrieved successfully."),
		500: OpenApiResponse(description="Profile not found.")
	}
)
@extend_schema(
	tags=["Profiles"],
	summary="Update user profile",
	description="Update the current user's profile information. Authentication required.",
	request={"application/json": {}},
	responses={
		200: OpenApiResponse(description="Profile updated successfully."),
		400: OpenApiResponse(description="Invalid input data.")
	}
)
class ProfileView(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		try:
			serializer = CurrentUserSerializer(request.user)
			return Response(serializer.data, status=status.HTTP_200_OK)
		except ProfileNotFound:
			return Response({"error": "Profile not found"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	def patch(self, request):
		serializer = UserProfileUpdateSerializer(request.user, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
	tags=["Profiles"],
	summary="Get candidate profile",
	description="Retrieve the candidate's profile information. Authentication required. Candidate only.",
	responses={
		200: OpenApiResponse(description="Candidate profile retrieved successfully."),
		403: OpenApiResponse(description="Only candidates can access their profile.")
	}
)
@extend_schema(
	tags=["Profiles"],
	summary="Update candidate profile",
	description="Update the candidate's profile information. Authentication required. Candidate only.",
	request={"application/json": {}},
	responses={
		200: OpenApiResponse(description="Candidate profile updated successfully."),
		400: OpenApiResponse(description="Invalid input data."),
		403: OpenApiResponse(description="Only candidates can update their profile.")
	}
)
class CandidateProfileView(APIView):
	permission_classes = (IsAuthenticated, IsCandidate)

	def get(self, request):
		profile = CandidateProfile.objects.select_related("user").get(user=request.user)
		serializer = CandidateProfileSerializer(profile)
		return Response(serializer.data, status=status.HTTP_200_OK)

	def patch(self, request):
		profile = CandidateProfile.objects.select_related("user").get(user=request.user)
		serializer = CandidateProfileUpdateSerializer(profile, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
	tags=["Profiles"],
	summary="Get recruiter profile",
	description="Retrieve the recruiter's profile information. Authentication required. Recruiter only.",
	responses={
		200: OpenApiResponse(description="Recruiter profile retrieved successfully."),
		403: OpenApiResponse(description="Only recruiters can access their profile.")
	}
)
@extend_schema(
	tags=["Profiles"],
	summary="Update recruiter profile",
	description="Update the recruiter's profile information. Authentication required. Recruiter only.",
	request={"application/json": {}},
	responses={
		200: OpenApiResponse(description="Recruiter profile updated successfully."),
		400: OpenApiResponse(description="Invalid input data."),
		403: OpenApiResponse(description="Only recruiters can update their profile.")
	}
)
class RecruiterProfileView(APIView):
	permission_classes = (IsAuthenticated, IsRecruiter)

	def get(self, request):
		profile = RecruiterProfile.objects.select_related("user").get(user=request.user)
		serializer = RecruiterProfileSerializer(profile)
		return Response(serializer.data, status=status.HTTP_200_OK)

	def patch(self, request):
		profile = RecruiterProfile.objects.select_related("user").get(user=request.user)
		serializer = RecruiterProfileUpdateSerializer(profile, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data, status=status.HTTP_200_OK)
