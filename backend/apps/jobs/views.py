from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from apps.users.permissions import IsRecruiter
from .models import Job
from .permissions import IsJobOwner
from .serializers import (
    JobCreateSerializer,
    JobUpdateSerializer,
    JobDetailSerializer,
    JobListSerializer,
    JobSearchSerializer,
    JobSearchPagination,
)
from matchhire_backend.core.validators import validate_uuid, validate_ordering, validate_search_length

User = get_user_model()


@extend_schema(
	tags=["Jobs"],
	summary="Create a new job",
	description="Create a new job posting. Authentication required. Recruiter only.",
	request=JobCreateSerializer,
	responses={
		201: JobDetailSerializer,
		400: OpenApiResponse(description="Invalid input data."),
		403: OpenApiResponse(description="Only recruiters can create jobs.")
	}
)
class JobCreateView(APIView):
    """
    Create a new job.
    
    POST /api/jobs/
    
    Authentication required. Recruiter only.
    """
    permission_classes = (IsAuthenticated, IsRecruiter)
    throttle_scope = 'authenticated'

    def post(self, request):
        """Create a new job"""
        serializer = JobCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        job = serializer.save()
        response_serializer = JobDetailSerializer(job)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
	tags=["Jobs"],
	summary="List my jobs",
	description="List all jobs for the current recruiter (draft, active, closed). Authentication required. Recruiter only.",
	responses={
		200: OpenApiResponse(description="Jobs retrieved successfully."),
		403: OpenApiResponse(description="Only recruiters can view their jobs.")
	}
)
class MyJobsListView(APIView):
    """
    List jobs for the current recruiter.
    
    GET /api/jobs/my/
    
    Authentication required. Recruiter only.
    Returns all jobs (draft, active, closed) owned by the recruiter.
    """
    permission_classes = (IsAuthenticated, IsRecruiter)
    throttle_scope = 'authenticated'

    def get(self, request):
        """List all jobs for the current recruiter"""
        jobs = Job.objects.filter(recruiter=request.user).select_related("recruiter").order_by("-created_at")
        serializer = JobListSerializer(jobs, many=True)
        return Response(serializer.data)


@extend_schema(
	tags=["Jobs"],
	summary="Get job details",
	description="Retrieve a specific job. Candidates can view ACTIVE jobs only. Recruiter owners can view own jobs (any status).",
	responses={
		200: OpenApiResponse(description="Job details retrieved successfully."),
		404: OpenApiResponse(description="Job not found.")
	}
)
@extend_schema(
	tags=["Jobs"],
	summary="Update job",
	description="Update job details. Recruiter owner only.",
	request={"application/json": {}},
	responses={
		200: OpenApiResponse(description="Job updated successfully."),
		403: OpenApiResponse(description="Only recruiters can update jobs."),
		404: OpenApiResponse(description="Job not found.")
	}
)
class JobDetailView(APIView):
    """
    Retrieve or update a specific job.
    
    GET /api/jobs/<id>/
    PATCH /api/jobs/<id>/
    
    GET: Authentication required.
         - Candidates: can view ACTIVE jobs only
         - Recruiter owner: can view own jobs (any status)
         - Other recruiters: can view ACTIVE jobs only
    
    PATCH: Authentication required. Recruiter owner only.
    """
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'authenticated'

    def get_object(self, request, id):
        """Get job with access control based on user role and ownership"""
        validate_uuid(id, "id")
        try:
            job = Job.objects.select_related("recruiter").get(id=id)
        except Job.DoesNotExist:
            raise Http404("Job not found")

        # Candidate: can only view ACTIVE jobs
        if request.user.role == User.Roles.CANDIDATE:
            if job.status != Job.JobStatus.ACTIVE:
                raise Http404("Job not found")
            return job

        # Recruiter owner: can view own jobs (any status)
        if job.recruiter == request.user:
            return job

        # Other recruiter: can only view ACTIVE jobs
        if job.status != Job.JobStatus.ACTIVE:
            raise Http404("Job not found")
        return job

    def get(self, request, id):
        """Retrieve job details"""
        job = self.get_object(request, id)
        serializer = JobDetailSerializer(job)
        return Response(serializer.data)

    def patch(self, request, id):
        """Update job details (recruiter owner only)"""
        if request.user.role != User.Roles.RECRUITER:
            return Response(
                {"detail": "Only recruiters can update jobs."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            job = Job.objects.select_related("recruiter").get(id=id, recruiter=request.user)
        except Job.DoesNotExist:
            raise Http404("Job not found")

        serializer = JobUpdateSerializer(
            job,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_serializer = JobDetailSerializer(job)
        return Response(response_serializer.data)


@extend_schema(
	tags=["Jobs"],
	summary="Close a job",
	description="Close a job posting. Recruiter owner only.",
	responses={
		200: JobDetailSerializer,
		400: OpenApiResponse(description="Job is already closed."),
		403: OpenApiResponse(description="Only recruiters can close jobs."),
		404: OpenApiResponse(description="Job not found.")
	}
)
class JobCloseView(APIView):
    """
    Close a job.
    
    POST /api/jobs/<id>/close/
    
    Authentication required. Recruiter only.
    Only owner can close their jobs.
    """
    permission_classes = (IsAuthenticated, IsRecruiter, IsJobOwner)
    throttle_scope = 'authenticated'
    serializer_class = JobDetailSerializer

    def get_object(self, request, id):
        """Get job if owned by current recruiter"""
        validate_uuid(id, "id")
        try:
            return Job.objects.select_related("recruiter").get(id=id, recruiter=request.user)
        except Job.DoesNotExist:
            raise Http404("Job not found")

    def post(self, request, id):
        """Close the job"""
        job = self.get_object(request, id)
        
        if job.status == Job.JobStatus.CLOSED:
            return Response(
                {"detail": "Job is already closed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        job.status = Job.JobStatus.CLOSED
        job.closed_at = timezone.now()
        job.save(update_fields=["status", "closed_at"])
        
        response_serializer = JobDetailSerializer(job)
        return Response(response_serializer.data)


@extend_schema(
	tags=["Jobs"],
	summary="List active jobs",
	description="List active jobs with search, filtering, and pagination. Returns only ACTIVE jobs.",
	parameters=[
		OpenApiParameter(name='q', description='Search query (title, company, description)', required=False, type=str),
		OpenApiParameter(name='location', description='Filter by location', required=False, type=str),
		OpenApiParameter(name='employment_type', description='Filter by employment type (full_time, part_time, contract, internship)', required=False, type=str),
		OpenApiParameter(name='experience_level', description='Filter by experience level (entry, junior, mid, senior, lead)', required=False, type=str),
		OpenApiParameter(name='is_remote', description='Filter by remote status (true/false)', required=False, type=bool),
		OpenApiParameter(name='salary_min', description='Filter by minimum salary', required=False, type=float),
		OpenApiParameter(name='salary_max', description='Filter by maximum salary', required=False, type=float),
		OpenApiParameter(name='ordering', description='Order by field (created_at, -created_at, salary_min, -salary_min, salary_max, -salary_max)', required=False, type=str),
		OpenApiParameter(name='page', description='Page number', required=False, type=int),
		OpenApiParameter(name='page_size', description='Page size (max 100)', required=False, type=int),
	],
	responses={
		200: OpenApiResponse(description="Jobs retrieved successfully with pagination."),
		400: OpenApiResponse(description="Invalid filter parameters.")
	}
)
class PublicJobListView(APIView):
    """
    List active jobs for candidates with search, filtering, and pagination.
    
    GET /api/jobs/
    
    Authentication required.
    Returns only ACTIVE jobs (no draft or closed jobs).
    
    Query parameters:
    - q: Search across title, company_name, description
    - location: Case-insensitive partial match
    - employment_type: full_time, part_time, contract, internship
    - experience_level: entry, junior, mid, senior, lead
    - is_remote: true/false
    - salary_min: Return jobs where salary_max >= requested_salary_min
    - salary_max: Return jobs where salary_min <= requested_salary_max
    - ordering: created_at, -created_at, salary_min, -salary_min, salary_max, -salary_max
    - page: Page number
    - page_size: Page size (max 100)
    """
    permission_classes = (IsAuthenticated,)
    pagination_class = JobSearchPagination
    throttle_scope = 'authenticated'

    def get(self, request):
        """List all active jobs with search, filtering, and pagination"""
        # Start with active jobs only
        queryset = Job.objects.filter(status=Job.JobStatus.ACTIVE)
        
        # Search across title, company_name, description
        q = request.query_params.get('q')
        if q:
            validate_search_length(q, max_length=200)
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(company_name__icontains=q) |
                Q(description__icontains=q)
            )
        
        # Filter by location (case-insensitive partial match)
        location = request.query_params.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # Filter by employment_type
        employment_type = request.query_params.get('employment_type')
        if employment_type:
            valid_employment_types = [choice[0] for choice in Job.EmploymentType.choices]
            if employment_type not in valid_employment_types:
                return Response(
                    {"detail": f"Invalid employment_type. Valid values: {', '.join(valid_employment_types)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            queryset = queryset.filter(employment_type=employment_type)
        
        # Filter by experience_level
        experience_level = request.query_params.get('experience_level')
        if experience_level:
            valid_experience_levels = [choice[0] for choice in Job.ExperienceLevel.choices]
            if experience_level not in valid_experience_levels:
                return Response(
                    {"detail": f"Invalid experience_level. Valid values: {', '.join(valid_experience_levels)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            queryset = queryset.filter(experience_level=experience_level)
        
        # Filter by is_remote
        is_remote = request.query_params.get('is_remote')
        if is_remote:
            if is_remote.lower() not in ['true', 'false']:
                return Response(
                    {"detail": "Invalid is_remote value. Must be 'true' or 'false'."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            queryset = queryset.filter(is_remote=(is_remote.lower() == 'true'))
        
        # Filter by salary_min (jobs where salary_max >= requested_salary_min)
        salary_min = request.query_params.get('salary_min')
        if salary_min:
            try:
                salary_min_value = float(salary_min)
                queryset = queryset.filter(salary_max__gte=salary_min_value)
            except (ValueError, TypeError):
                return Response(
                    {"detail": "Invalid salary_min value. Must be a number."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Filter by salary_max (jobs where salary_min <= requested_salary_max)
        salary_max = request.query_params.get('salary_max')
        if salary_max:
            try:
                salary_max_value = float(salary_max)
                queryset = queryset.filter(salary_min__lte=salary_max_value)
            except (ValueError, TypeError):
                return Response(
                    {"detail": "Invalid salary_max value. Must be a number."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Ordering
        ordering = request.query_params.get('ordering', '-created_at')
        valid_ordering_fields = ['created_at', '-created_at', 'salary_min', '-salary_min', 'salary_max', '-salary_max']
        validate_ordering(ordering, valid_ordering_fields)
        queryset = queryset.order_by(ordering)
        
        # Query optimization
        queryset = queryset.select_related("recruiter")
        
        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = JobSearchSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = JobSearchSerializer(queryset, many=True)
        return Response(serializer.data)
