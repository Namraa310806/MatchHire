from django.contrib.auth import get_user_model
from django.http import Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsRecruiter
from .models import Job
from .permissions import IsJobOwner
from .serializers import (
    JobCreateSerializer,
    JobUpdateSerializer,
    JobDetailSerializer,
    JobListSerializer,
)

User = get_user_model()


class JobCreateView(APIView):
    """
    Create a new job.
    
    POST /api/jobs/
    
    Authentication required. Recruiter only.
    """
    permission_classes = (IsAuthenticated, IsRecruiter)

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


class MyJobsListView(APIView):
    """
    List jobs for the current recruiter.
    
    GET /api/jobs/my/
    
    Authentication required. Recruiter only.
    Returns all jobs (draft, active, closed) owned by the recruiter.
    """
    permission_classes = (IsAuthenticated, IsRecruiter)

    def get(self, request):
        """List all jobs for the current recruiter"""
        jobs = Job.objects.filter(recruiter=request.user).select_related("recruiter").order_by("-created_at")
        serializer = JobListSerializer(jobs, many=True)
        return Response(serializer.data)


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

    def get_object(self, request, id):
        """Get job with access control based on user role and ownership"""
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


class JobCloseView(APIView):
    """
    Close a job.
    
    POST /api/jobs/<id>/close/
    
    Authentication required. Recruiter only.
    Only owner can close their jobs.
    """
    permission_classes = (IsAuthenticated, IsRecruiter, IsJobOwner)

    def get_object(self, request, id):
        """Get job if owned by current recruiter"""
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


class PublicJobListView(APIView):
    """
    List active jobs for candidates.
    
    GET /api/jobs/
    
    Authentication required.
    Returns only ACTIVE jobs (no draft or closed jobs).
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """List all active jobs"""
        jobs = Job.objects.filter(
            status=Job.JobStatus.ACTIVE
        ).select_related("recruiter").order_by("-created_at")
        serializer = JobListSerializer(jobs, many=True)
        return Response(serializer.data)
