from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import CandidateProfile, RecruiterProfile


class UserModelTests(TestCase):
	def test_candidate_profile_is_created_automatically(self):
		user = get_user_model().objects.create_user(
			email="candidate@example.com",
			password="pass12345",
			full_name="Candidate One",
		)

		self.assertEqual(user.role, get_user_model().Roles.CANDIDATE)
		self.assertTrue(CandidateProfile.objects.filter(user=user).exists())

	def test_recruiter_profile_is_created_automatically(self):
		user = get_user_model().objects.create_user(
			email="recruiter@example.com",
			password="pass12345",
			full_name="Recruiter One",
			role=get_user_model().Roles.RECRUITER,
		)

		self.assertTrue(RecruiterProfile.objects.filter(user=user).exists())

	def test_create_superuser_enables_admin_login(self):
		user = get_user_model().objects.create_superuser(
			email="admin@example.com",
			password="pass12345",
			full_name="Admin User",
		)

		self.assertTrue(user.is_staff)
		self.assertTrue(user.is_superuser)
		self.assertTrue(self.client.login(username="admin@example.com", password="pass12345"))
