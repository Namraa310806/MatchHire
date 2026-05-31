from rest_framework import serializers

from .models import CandidateProfile, RecruiterProfile, User


class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = (
			"id",
			"email",
			"full_name",
			"role",
			"is_active",
			"is_staff",
			"is_verified",
			"date_joined",
			"updated_at",
		)
		read_only_fields = ("id", "is_active", "is_staff", "is_verified", "date_joined", "updated_at")


class CandidateProfileSerializer(serializers.ModelSerializer):
	class Meta:
		model = CandidateProfile
		fields = (
			"id",
			"user",
			"headline",
			"bio",
			"current_location",
			"years_of_experience",
			"skills_text",
			"linkedin_url",
			"github_url",
			"portfolio_url",
			"resume_uploaded",
			"created_at",
			"updated_at",
		)
		read_only_fields = ("id", "created_at", "updated_at")


class RecruiterProfileSerializer(serializers.ModelSerializer):
	class Meta:
		model = RecruiterProfile
		fields = (
			"id",
			"user",
			"company_name",
			"company_website",
			"job_title",
			"verified_company",
			"created_at",
			"updated_at",
		)
		read_only_fields = ("id", "created_at", "updated_at")
