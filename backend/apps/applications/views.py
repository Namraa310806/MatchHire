from django.contrib.auth import get_user_model
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.jobs.models import Job
from apps.resumes.models import ResumeVersion
from apps.users.permissions import IsCandidate, IsRecruiter
from .models import Application
from .serializers import (
    ApplicationCreateSerializer,
    ApplicationListSerializer,
    ApplicationDetailSerializer,
)

User = get_user_model()


class JobApplyView(APIView):
    """
    Apply to a job.
    
    POST /api/jobs/<job_id>/apply/
    
    Authentication required. Candidate only.
    """
    permission_classes = (IsAuthenticated, IsCandidate)

    def post(self, request, job_id):
        """Apply to a job with a specific resume version"""
        # Get job
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            raise Http404("Job not found")

        # Check job status - only ACTIVE jobs can be applied to
        if job.status != Job.JobStatus.ACTIVE:
            return Response(
                {"detail": "Cannot apply to draft or closed jobs."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get resume_version_id from request
        resume_version_id = request.data.get("resume_version_id")
        if not resume_version_id:
            return Response(
                {"detail": "resume_version_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get resume version and verify ownership
        try:
            resume_version = ResumeVersion.objects.get(id=resume_version_id)
        except ResumeVersion.DoesNotExist:
            return Response(
                {"detail": "Resume version not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify resume version belongs to candidate
        if resume_version.resume.user != request.user:
            return Response(
                {"detail": "Resume version does not belong to you."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if already applied
        if Application.objects.filter(job=job, candidate=request.user).exists():
            return Response(
                {"detail": "You have already applied to this job."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create application
        serializer = ApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = Application.objects.create(
            job=job,
            candidate=request.user,
            resume_version=resume_version,
        )

        response_serializer = ApplicationDetailSerializer(application)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class MyApplicationsListView(APIView):
    """
    List applications for the current candidate.
    
    GET /api/applications/my/
    
    Authentication required. Candidate only.
    Returns only applications belonging to request.user.
    """
    permission_classes = (IsAuthenticated, IsCandidate)

    def get(self, request):
        """List all applications for the current candidate"""
        applications = Application.objects.filter(
            candidate=request.user
        ).select_related(
            "job",
            "candidate",
            "resume_version"
        ).order_by("-created_at")
        serializer = ApplicationListSerializer(applications, many=True)
        return Response(serializer.data)


class ApplicationDetailView(APIView):
    """
    Retrieve a specific application.
    
    GET /api/applications/<id>/
    
    Authentication required.
    - Candidate: can view own application
    - Recruiter: can view application only if application.job.recruiter == request.user
    - Everyone else: denied
    """
    permission_classes = (IsAuthenticated,)

    def get_object(self, request, id):
        """Get application with access control"""
        try:
            application = Application.objects.select_related(
                "job",
                "candidate",
                "resume_version"
            ).get(id=id)
        except Application.DoesNotExist:
            raise Http404("Application not found")

        # Candidate: can view own application
        if request.user.role == User.Roles.CANDIDATE:
            if application.candidate != request.user:
                raise Http404("Application not found")
            return application

        # Recruiter: can view application only if job belongs to them
        if request.user.role == User.Roles.RECRUITER:
            if application.job.recruiter != request.user:
                raise Http404("Application not found")
            return application

        # Everyone else: denied
        raise Http404("Application not found")

    def get(self, request, id):
        """Retrieve application details"""
        application = self.get_object(request, id)
        serializer = ApplicationDetailSerializer(application)
        return Response(serializer.data)


class JobApplicationsListView(APIView):
    """
    List applications for a specific job.
    
    GET /api/jobs/<job_id>/applications/
    
    Authentication required. Recruiter owner only.
    Returns all applications for that job.
    """
    permission_classes = (IsAuthenticated, IsRecruiter)

    def get_object(self, request, job_id):
        """Get job if owned by current recruiter"""
        try:
            job = Job.objects.get(id=job_id, recruiter=request.user)
        except Job.DoesNotExist:
            raise Http404("Job not found")
        return job

    def get(self, request, job_id):
        """List all applications for the job"""
        job = self.get_object(request, job_id)
        applications = Application.objects.filter(
            job=job
        ).select_related(
            "job",
            "candidate",
            "resume_version"
        ).order_by("-created_at")
        serializer = ApplicationListSerializer(applications, many=True)
        return Response(serializer.data)
