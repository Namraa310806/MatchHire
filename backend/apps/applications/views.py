from django.contrib.auth import get_user_model
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample

from apps.jobs.models import Job
from apps.resumes.models import ResumeVersion
from apps.users.permissions import IsCandidate, IsRecruiter
from .models import Application
from .serializers import (
    ApplicationCreateSerializer,
    ApplicationListSerializer,
    ApplicationDetailSerializer,
    ApplicationStatusUpdateSerializer,
    ApplicationStatusHistorySerializer,
)
from .services.workflow import ApplicationWorkflowService
from matchhire_backend.core.validators import validate_uuid

User = get_user_model()


@extend_schema(
	tags=["Applications"],
	summary="Apply to job",
	description="Apply to a job with a specific resume version. Authentication required. Candidate only.",
	request={
		"application/json": {
			"type": "object",
			"properties": {
				"resume_version_id": {"type": "string", "format": "uuid"}
			},
			"required": ["resume_version_id"]
		}
	},
	responses={
		201: OpenApiResponse(description="Application created successfully."),
		400: OpenApiResponse(description="Invalid request or already applied."),
		404: OpenApiResponse(description="Job or resume version not found.")
	},
	examples=[
		OpenApiExample(
			"Apply to job",
			value={"resume_version_id": "123e4567-e89b-12d3-a456-426614174000"},
			response_only=False,
		),
	]
)
class JobApplyView(APIView):
    """
    Apply to a job.
    
    POST /api/jobs/<job_id>/apply/
    
    Authentication required. Candidate only.
    """
    permission_classes = (IsAuthenticated, IsCandidate)
    throttle_scope = 'job_apply'

    def post(self, request, job_id):
        """Apply to a job with a specific resume version"""
        validate_uuid(job_id, "job_id")
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


@extend_schema(
	tags=["Applications"],
	summary="List my applications",
	description="List all applications for the current candidate. Authentication required. Candidate only.",
	responses={
		200: OpenApiResponse(description="Applications retrieved successfully."),
		403: OpenApiResponse(description="Only candidates can view their applications.")
	}
)
class MyApplicationsListView(APIView):
    """
    List applications for the current candidate.
    
    GET /api/applications/my/
    
    Authentication required. Candidate only.
    Returns only applications belonging to request.user.
    """
    permission_classes = (IsAuthenticated, IsCandidate)
    throttle_scope = 'authenticated'

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


@extend_schema(
	tags=["Applications"],
	summary="Get application details",
	description="Retrieve a specific application. Candidates can view own applications. Recruiters can view applications for their jobs.",
	responses={
		200: OpenApiResponse(description="Application details retrieved successfully."),
		404: OpenApiResponse(description="Application not found.")
	}
)
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
    throttle_scope = 'authenticated'

    def get_object(self, request, id):
        """Get application with access control"""
        validate_uuid(id, "id")
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


@extend_schema(
	tags=["Applications"],
	summary="List job applications",
	description="List all applications for a specific job. Recruiter owner only. Supports status filtering.",
	parameters=[
		OpenApiParameter(name='status', description='Filter by application status', required=False, type=str),
	],
	responses={
		200: OpenApiResponse(description="Applications retrieved successfully."),
		400: OpenApiResponse(description="Invalid status filter."),
		403: OpenApiResponse(description="Only recruiters can view job applications."),
		404: OpenApiResponse(description="Job not found.")
	}
)
class JobApplicationsListView(APIView):
    """
    List applications for a specific job.
    
    GET /api/jobs/<job_id>/applications/
    
    Authentication required. Recruiter owner only.
    Returns all applications for that job.
    Supports ?status= filtering.
    """
    permission_classes = (IsAuthenticated, IsRecruiter)
    throttle_scope = 'authenticated'

    def get_object(self, request, job_id):
        """Get job if owned by current recruiter"""
        validate_uuid(job_id, "job_id")
        try:
            job = Job.objects.get(id=job_id, recruiter=request.user)
        except Job.DoesNotExist:
            raise Http404("Job not found")
        return job

    def get(self, request, job_id):
        """List all applications for the job with optional status filtering"""
        job = self.get_object(request, job_id)
        
        # Get status filter from query params
        status_filter = request.query_params.get("status")
        
        # Validate status filter
        if status_filter:
            valid_statuses = [choice[0] for choice in Application.ApplicationStatus.choices]
            if status_filter not in valid_statuses:
                return Response(
                    {"detail": "Invalid status."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        # Build queryset
        applications = Application.objects.filter(job=job)
        
        # Apply status filter if provided
        if status_filter:
            applications = applications.filter(status=status_filter)
        
        applications = applications.select_related(
            "job",
            "candidate",
            "resume_version"
        ).order_by("-created_at")
        
        serializer = ApplicationListSerializer(applications, many=True)
        return Response(serializer.data)


@extend_schema(
	tags=["Applications"],
	summary="Update application status",
	description="Update application status. Recruiter only. Recruiter must own the job.",
	request={"application/json": {}},
	responses={
		200: OpenApiResponse(description="Application status updated successfully."),
		400: OpenApiResponse(description="Invalid status transition."),
		403: OpenApiResponse(description="Only recruiters can update application status."),
		404: OpenApiResponse(description="Application not found.")
	},
	examples=[
		OpenApiExample(
			"Update application status",
			value={"status": "shortlisted"},
			response_only=False,
		),
	]
)
class ApplicationStatusUpdateView(APIView):
    """
    Update application status.
    
    PATCH /api/applications/<id>/status/
    
    Authentication required. Recruiter only.
    Recruiter must own the job attached to the application.
    """
    permission_classes = (IsAuthenticated, IsRecruiter)
    throttle_scope = 'authenticated'

    def get_object(self, request, id):
        """Get application if job is owned by current recruiter"""
        validate_uuid(id, "id")
        try:
            application = Application.objects.select_related(
                "job",
                "candidate",
                "resume_version"
            ).get(id=id)
        except Application.DoesNotExist:
            raise Http404("Application not found")

        # Recruiter can only update applications for their own jobs
        if application.job.recruiter != request.user:
            raise Http404("Application not found")

        return application

    def patch(self, request, id):
        """Update application status"""
        application = self.get_object(request, id)
        
        serializer = ApplicationStatusUpdateSerializer(
            application,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        
        # Use service layer to change status
        try:
            updated_application = ApplicationWorkflowService.change_status(
                application,
                serializer.validated_data["status"],
                request.user
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        response_serializer = ApplicationDetailSerializer(updated_application)
        return Response(response_serializer.data)


@extend_schema(
	tags=["Applications"],
	summary="Get application history",
	description="Retrieve application status history. Candidates can view own application history. Recruiters can view history for their jobs.",
	responses={
		200: OpenApiResponse(description="Application history retrieved successfully."),
		404: OpenApiResponse(description="Application not found.")
	}
)
class ApplicationHistoryView(APIView):
    """
    Retrieve application status history.
    
    GET /api/applications/<id>/history/
    
    Authentication required.
    - Candidate: can view history of own application only.
    - Recruiter: can view history only if they own the job.
    """
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'authenticated'

    def get_object(self, request, id):
        """Get application with access control"""
        validate_uuid(id, "id")
        try:
            application = Application.objects.select_related(
                "job",
                "candidate",
                "resume_version"
            ).get(id=id)
        except Application.DoesNotExist:
            raise Http404("Application not found")

        # Candidate: can view own application history
        if request.user.role == User.Roles.CANDIDATE:
            if application.candidate != request.user:
                raise Http404("Application not found")
            return application

        # Recruiter: can view history only if job belongs to them
        if request.user.role == User.Roles.RECRUITER:
            if application.job.recruiter != request.user:
                raise Http404("Application not found")
            return application

        # Everyone else: denied
        raise Http404("Application not found")

    def get(self, request, id):
        """Retrieve application status history"""
        application = self.get_object(request, id)
        
        history = application.status_history.select_related(
            "changed_by"
        ).order_by("-changed_at")
        
        serializer = ApplicationStatusHistorySerializer(history, many=True)
        return Response(serializer.data)
