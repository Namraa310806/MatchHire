from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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
