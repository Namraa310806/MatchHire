from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.validators import ValidationError

from .models import CandidateProfile, RecruiterProfile, User


class ProfileNotFound(Exception):
	pass


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


class MeUserSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = (
			"id",
			"email",
			"full_name",
			"role",
			"is_verified",
			"date_joined",
		)
		read_only_fields = ("id", "is_verified", "date_joined")


class LoginSerializer(serializers.Serializer):
	email = serializers.EmailField()
	password = serializers.CharField(write_only=True, trim_whitespace=False)

	def validate_email(self, value):
		if not value:
			raise serializers.ValidationError("Email is required.")
		return value

	def validate_password(self, value):
		if not value:
			raise serializers.ValidationError("Password is required.")
		return value


class BaseRegistrationSerializer(serializers.Serializer):
	email = serializers.EmailField()
	password = serializers.CharField(write_only=True, trim_whitespace=False)
	confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)
	full_name = serializers.CharField(max_length=255)
	role = None

	def validate_email(self, value):
		if not value:
			raise serializers.ValidationError("Email is required.")

		normalized_email = User.objects.normalize_email(value)
		if User.objects.filter(email__iexact=normalized_email).exists():
			raise serializers.ValidationError("A user with this email already exists.")
		return normalized_email

	def validate(self, attrs):
		if attrs["password"] != attrs["confirm_password"]:
			raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

		password_user = User(
			email=attrs["email"],
			full_name=attrs["full_name"],
			role=self.role or User.Roles.CANDIDATE,
		)
		try:
			validate_password(attrs["password"], user=password_user)
		except DjangoValidationError as exc:
			raise serializers.ValidationError({"password": list(exc.messages)})

		return attrs

	def create(self, validated_data):
		validated_data.pop("confirm_password")
		return User.objects.create_user(
			email=validated_data["email"],
			password=validated_data["password"],
			full_name=validated_data["full_name"],
			role=self.role,
		)


class CandidateRegistrationSerializer(BaseRegistrationSerializer):
	role = User.Roles.CANDIDATE


class RecruiterRegistrationSerializer(BaseRegistrationSerializer):
	role = User.Roles.RECRUITER
	company_name = serializers.CharField(max_length=255)

	def create(self, validated_data):
		company_name = validated_data.pop("company_name")
		user = super().create(validated_data)
		profile = user.recruiter_profile
		profile.company_name = company_name
		profile.save(update_fields=["company_name"])
		return user


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


class CurrentUserSerializer(serializers.Serializer):
	user = serializers.SerializerMethodField()
	profile = serializers.SerializerMethodField()

	def get_user(self, obj):
		return MeUserSerializer(obj).data

	def get_profile(self, obj):
		if obj.role == User.Roles.CANDIDATE:
			try:
				return CandidateProfileSerializer(obj.candidate_profile).data
			except CandidateProfile.DoesNotExist:
				raise ProfileNotFound("Profile not found")
		elif obj.role == User.Roles.RECRUITER:
			try:
				return RecruiterProfileSerializer(obj.recruiter_profile).data
			except RecruiterProfile.DoesNotExist:
				raise ProfileNotFound("Profile not found")
		return None


class UserProfileUpdateSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = ("full_name",)

	def validate(self, attrs):
		unknown_fields = set(self.initial_data.keys()) - set(self.fields.keys())
		if unknown_fields:
			raise ValidationError(f"Unknown field(s): {', '.join(unknown_fields)}")
		return attrs


class CandidateProfileUpdateSerializer(serializers.ModelSerializer):
	class Meta:
		model = CandidateProfile
		fields = (
			"headline",
			"bio",
			"current_location",
			"years_of_experience",
			"skills_text",
			"linkedin_url",
			"github_url",
			"portfolio_url",
		)
		read_only_fields = ("id", "user", "resume_uploaded", "created_at", "updated_at")

	def validate_years_of_experience(self, value):
		if value < 0:
			raise ValidationError("years_of_experience must be >= 0")
		return value


class RecruiterProfileUpdateSerializer(serializers.ModelSerializer):
	class Meta:
		model = RecruiterProfile
		fields = (
			"company_name",
			"company_website",
			"job_title",
		)
		read_only_fields = ("id", "user", "verified_company", "created_at", "updated_at")
