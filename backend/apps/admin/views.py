from django.db.models import Q
from django.http import Http404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.admin.permissions import IsAdmin
from apps.admin.serializers import (
    AdminApplicationSerializer,
    AdminDashboardSerializer,
    AdminJobSerializer,
    AdminJobUpdateSerializer,
    AdminResumeSerializer,
    AdminResumeUpdateSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
)
from apps.admin.services import AdminModerationService
from apps.applications.models import Application
from apps.jobs.models import Job
from apps.resumes.models import Resume
from apps.users.models import User


class AdminPagination(PageNumberPagination):
    """Pagination for admin endpoints"""
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class AdminUserListView(APIView):
    """
    List all users with filtering and pagination.
    
    GET /api/admin/users/
    
    Admin only.
    Filters: role, is_active, search (name/email)
    Ordering: email, full_name, date_joined, -date_joined
    """
    permission_classes = (IsAdmin,)
    pagination_class = AdminPagination

    def get(self, request):
        """List all users with filtering and ordering"""
        queryset = User.objects.all()

        # Filter by role
        role = request.query_params.get("role")
        if role:
            valid_roles = [choice[0] for choice in User.Roles.choices]
            if role not in valid_roles:
                return Response(
                    {"detail": f"Invalid role. Valid values: {', '.join(valid_roles)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(role=role)

        # Filter by is_active
        is_active = request.query_params.get("is_active")
        if is_active:
            if is_active.lower() not in ["true", "false"]:
                return Response(
                    {"detail": "Invalid is_active value. Must be 'true' or 'false'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(is_active=(is_active.lower() == "true"))

        # Search by name or email
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) | Q(full_name__icontains=search)
            )

        # Ordering
        ordering = request.query_params.get("ordering", "-date_joined")
        valid_ordering_fields = ["email", "full_name", "date_joined", "-date_joined"]
        if ordering not in valid_ordering_fields:
            return Response(
                {"detail": f"Invalid ordering. Valid values: {', '.join(valid_ordering_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        queryset = queryset.order_by(ordering)

        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = AdminUserSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = AdminUserSerializer(queryset, many=True)
        return Response(serializer.data)


class AdminUserDetailView(APIView):
    """
    Retrieve or update a specific user.
    
    GET /api/admin/users/<id>/
    PATCH /api/admin/users/<id>/
    
    Admin only.
    GET: Retrieve user details
    PATCH: Update is_active and role fields
    """
    permission_classes = (IsAdmin,)

    def get_object(self, id):
        """Get user by id"""
        try:
            return User.objects.get(id=id)
        except User.DoesNotExist:
            raise Http404("User not found")

    def get(self, request, id):
        """Retrieve user details"""
        user = self.get_object(id)
        serializer = AdminUserSerializer(user)
        return Response(serializer.data)

    def patch(self, request, id):
        """Update user (is_active, role)"""
        user = self.get_object(id)

        serializer = AdminUserUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Use service layer for update with moderation logging
        updated_user = AdminModerationService.update_user(
            user_id=user.id,
            is_active=serializer.validated_data.get("is_active"),
            role=serializer.validated_data.get("role"),
            admin_user=request.user,
            reason=serializer.validated_data.get("reason", ""),
        )

        response_serializer = AdminUserSerializer(updated_user)
        return Response(response_serializer.data)


class AdminJobListView(APIView):
    """
    List all jobs with filtering and pagination.
    
    GET /api/admin/jobs/
    
    Admin only.
    Returns ALL jobs (draft, active, closed).
    Filters: status, company, recruiter_id, search
    Ordering: created_at, -created_at, title, -title
    """
    permission_classes = (IsAdmin,)
    pagination_class = AdminPagination

    def get(self, request):
        """List all jobs with filtering and ordering"""
        queryset = Job.objects.select_related("recruiter")

        # Filter by status
        status_filter = request.query_params.get("status")
        if status_filter:
            valid_statuses = [choice[0] for choice in Job.JobStatus.choices]
            if status_filter not in valid_statuses:
                return Response(
                    {"detail": f"Invalid status. Valid values: {', '.join(valid_statuses)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(status=status_filter)

        # Filter by company
        company = request.query_params.get("company")
        if company:
            queryset = queryset.filter(company_name__icontains=company)

        # Filter by recruiter_id
        recruiter_id = request.query_params.get("recruiter_id")
        if recruiter_id:
            queryset = queryset.filter(recruiter_id=recruiter_id)

        # Search by title or company
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(company_name__icontains=search)
            )

        # Ordering
        ordering = request.query_params.get("ordering", "-created_at")
        valid_ordering_fields = ["created_at", "-created_at", "title", "-title"]
        if ordering not in valid_ordering_fields:
            return Response(
                {"detail": f"Invalid ordering. Valid values: {', '.join(valid_ordering_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        queryset = queryset.order_by(ordering)

        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = AdminJobSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = AdminJobSerializer(queryset, many=True)
        return Response(serializer.data)


class AdminJobDetailView(APIView):
    """
    Update a specific job status.
    
    PATCH /api/admin/jobs/<id>/
    
    Admin only.
    Update job status with moderation logging.
    """
    permission_classes = (IsAdmin,)

    def get_object(self, id):
        """Get job by id"""
        try:
            return Job.objects.select_related("recruiter").get(id=id)
        except Job.DoesNotExist:
            raise Http404("Job not found")

    def patch(self, request, id):
        """Update job status"""
        job = self.get_object(id)

        serializer = AdminJobUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Use service layer for update with moderation logging
        updated_job = AdminModerationService.update_job(
            job_id=job.id,
            status=serializer.validated_data.get("status"),
            admin_user=request.user,
            reason=serializer.validated_data.get("reason", ""),
        )

        response_serializer = AdminJobSerializer(updated_job)
        return Response(response_serializer.data)


class AdminResumeListView(APIView):
    """
    List all resumes with filtering and pagination.
    
    GET /api/admin/resumes/
    
    Admin only.
    Filters: candidate_id, parsed (has current version), structured (has structured data)
    Ordering: created_at, -created_at
    """
    permission_classes = (IsAdmin,)
    pagination_class = AdminPagination

    def get(self, request):
        """List all resumes with filtering and ordering"""
        queryset = Resume.objects.select_related("user")

        # Filter by candidate_id
        candidate_id = request.query_params.get("candidate_id")
        if candidate_id:
            queryset = queryset.filter(user_id=candidate_id)

        # Filter by parsed (has current version)
        parsed = request.query_params.get("parsed")
        if parsed:
            if parsed.lower() not in ["true", "false"]:
                return Response(
                    {"detail": "Invalid parsed value. Must be 'true' or 'false'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if parsed.lower() == "true":
                queryset = queryset.filter(versions__is_current=True).distinct()
            else:
                queryset = queryset.exclude(versions__is_current=True).distinct()

        # Filter by structured (has structured resume on current version)
        structured = request.query_params.get("structured")
        if structured:
            if structured.lower() not in ["true", "false"]:
                return Response(
                    {"detail": "Invalid structured value. Must be 'true' or 'false'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if structured.lower() == "true":
                queryset = queryset.filter(
                    versions__is_current=True, versions__structured_resume__isnull=False
                ).distinct()
            else:
                queryset = queryset.exclude(
                    versions__is_current=True, versions__structured_resume__isnull=False
                ).distinct()

        # Ordering
        ordering = request.query_params.get("ordering", "-created_at")
        valid_ordering_fields = ["created_at", "-created_at"]
        if ordering not in valid_ordering_fields:
            return Response(
                {"detail": f"Invalid ordering. Valid values: {', '.join(valid_ordering_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        queryset = queryset.order_by(ordering)

        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = AdminResumeSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = AdminResumeSerializer(queryset, many=True)
        return Response(serializer.data)


class AdminResumeDetailView(APIView):
    """
    Update a specific resume (activate/deactivate user).
    
    PATCH /api/admin/resumes/<id>/
    
    Admin only.
    Update user is_active status with moderation logging.
    """
    permission_classes = (IsAdmin,)

    def get_object(self, id):
        """Get resume by id"""
        try:
            return Resume.objects.select_related("user").get(id=id)
        except Resume.DoesNotExist:
            raise Http404("Resume not found")

    def patch(self, request, id):
        """Update resume (activate/deactivate user)"""
        resume = self.get_object(id)

        serializer = AdminResumeUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Use service layer for update with moderation logging
        updated_resume = AdminModerationService.update_resume(
            resume_id=resume.id,
            is_active=serializer.validated_data.get("is_active"),
            admin_user=request.user,
            reason=serializer.validated_data.get("reason", ""),
        )

        response_serializer = AdminResumeSerializer(updated_resume)
        return Response(response_serializer.data)


class AdminApplicationListView(APIView):
    """
    List all applications with filtering and pagination (read-only).
    
    GET /api/admin/applications/
    
    Admin only.
    Read-only inspection. No status editing.
    Filters: status, candidate_id, job_id, recruiter_id
    Ordering: created_at, -created_at
    """
    permission_classes = (IsAdmin,)
    pagination_class = AdminPagination

    def get(self, request):
        """List all applications with filtering and ordering"""
        queryset = Application.objects.select_related(
            "job", "candidate", "resume_version", "job__recruiter"
        )

        # Filter by status
        status_filter = request.query_params.get("status")
        if status_filter:
            valid_statuses = [choice[0] for choice in Application.ApplicationStatus.choices]
            if status_filter not in valid_statuses:
                return Response(
                    {"detail": f"Invalid status. Valid values: {', '.join(valid_statuses)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(status=status_filter)

        # Filter by candidate_id
        candidate_id = request.query_params.get("candidate_id")
        if candidate_id:
            queryset = queryset.filter(candidate_id=candidate_id)

        # Filter by job_id
        job_id = request.query_params.get("job_id")
        if job_id:
            queryset = queryset.filter(job_id=job_id)

        # Filter by recruiter_id
        recruiter_id = request.query_params.get("recruiter_id")
        if recruiter_id:
            queryset = queryset.filter(job__recruiter_id=recruiter_id)

        # Ordering
        ordering = request.query_params.get("ordering", "-created_at")
        valid_ordering_fields = ["created_at", "-created_at"]
        if ordering not in valid_ordering_fields:
            return Response(
                {"detail": f"Invalid ordering. Valid values: {', '.join(valid_ordering_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        queryset = queryset.order_by(ordering)

        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = AdminApplicationSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = AdminApplicationSerializer(queryset, many=True)
        return Response(serializer.data)


class AdminDashboardView(APIView):
    """
    Get platform statistics.
    
    GET /api/admin/dashboard/
    
    Admin only.
    Returns aggregated platform statistics.
    """
    permission_classes = (IsAdmin,)

    def get(self, request):
        """Get platform statistics"""
        stats = AdminModerationService.dashboard()
        serializer = AdminDashboardSerializer(stats)
        return Response(serializer.data)
