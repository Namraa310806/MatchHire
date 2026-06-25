from django.contrib.auth import get_user_model
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.models import Application
from apps.users.permissions import IsCandidate, IsRecruiter
from .models import Interview
from .serializers import (
    InterviewCreateSerializer,
    InterviewDetailSerializer,
    InterviewListSerializer,
    InterviewStatusUpdateSerializer,
    InterviewStatusHistorySerializer,
)
from .services.workflow import InterviewWorkflowService

User = get_user_model()


class ApplicationInterviewsListView(APIView):
    """
    List or create interviews for a specific application.

    GET /api/applications/<id>/interviews/
    POST /api/applications/<id>/interviews/

    Authentication required.
    - GET: Candidate (own application only) or Recruiter (own job only)
    - POST: Recruiter only, must own the job
    """

    permission_classes = (IsAuthenticated,)

    def get_object(self, request, application_id):
        """Get application with access control"""
        try:
            application = Application.objects.select_related(
                "job",
                "candidate",
                "resume_version"
            ).get(id=application_id)
        except Application.DoesNotExist:
            raise Http404("Application not found")

        # Candidate: can view own application interviews
        if request.user.role == User.Roles.CANDIDATE:
            if application.candidate != request.user:
                raise Http404("Application not found")
            return application

        # Recruiter: can view interviews only if job belongs to them
        if request.user.role == User.Roles.RECRUITER:
            if application.job.recruiter != request.user:
                raise Http404("Application not found")
            return application

        # Everyone else: denied
        raise Http404("Application not found")

    def get(self, request, application_id):
        """List interviews for the application"""
        application = self.get_object(request, application_id)

        interviews = application.interviews.select_related(
            "application",
            "application__candidate",
            "application__job",
            "created_by",
        ).order_by("scheduled_at")

        serializer = InterviewListSerializer(interviews, many=True)
        return Response(serializer.data)

    def post(self, request, application_id):
        """Schedule an interview for the application"""
        # Recruiter only
        if request.user.role != User.Roles.RECRUITER:
            return Response(
                {"detail": "Only recruiters can schedule interviews."},
                status=status.HTTP_403_FORBIDDEN,
            )

        application = self.get_object(request, application_id)

        # Validate application status
        allowed_statuses = [
            Application.ApplicationStatus.UNDER_REVIEW,
            Application.ApplicationStatus.SHORTLISTED,
        ]

        if application.status not in allowed_statuses:
            return Response(
                {
                    "detail": f"Cannot schedule interview for application with status '{application.status}'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = InterviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        interview = Interview.objects.create(
            application=application,
            created_by=request.user,
            **serializer.validated_data,
        )

        response_serializer = InterviewDetailSerializer(interview)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class InterviewDetailView(APIView):
    """
    Retrieve a specific interview.

    GET /api/interviews/<id>/

    Authentication required.
    - Candidate: can view own interview only
    - Recruiter: can view interview only if application.job.recruiter == request.user
    """

    permission_classes = (IsAuthenticated,)

    def get_object(self, request, interview_id):
        """Get interview with access control"""
        try:
            interview = Interview.objects.select_related(
                "application",
                "application__candidate",
                "application__job",
                "created_by",
            ).get(id=interview_id)
        except Interview.DoesNotExist:
            raise Http404("Interview not found")

        # Candidate: can view own interview
        if request.user.role == User.Roles.CANDIDATE:
            if interview.application.candidate != request.user:
                raise Http404("Interview not found")
            return interview

        # Recruiter: can view interview only if job belongs to them
        if request.user.role == User.Roles.RECRUITER:
            if interview.application.job.recruiter != request.user:
                raise Http404("Interview not found")
            return interview

        # Everyone else: denied
        raise Http404("Interview not found")

    def get(self, request, interview_id):
        """Retrieve interview details"""
        interview = self.get_object(request, interview_id)
        serializer = InterviewDetailSerializer(interview)
        return Response(serializer.data)


class InterviewStatusUpdateView(APIView):
    """
    Update interview status.

    PATCH /api/interviews/<id>/status/

    Authentication required. Recruiter only.
    Recruiter must own the job attached to the interview's application.
    """

    permission_classes = (IsAuthenticated, IsRecruiter)

    def get_object(self, request, interview_id):
        """Get interview if job is owned by current recruiter"""
        try:
            interview = Interview.objects.select_related(
                "application",
                "application__job",
                "application__candidate",
                "created_by",
            ).get(id=interview_id)
        except Interview.DoesNotExist:
            raise Http404("Interview not found")

        # Recruiter can only update interviews for their own jobs
        if interview.application.job.recruiter != request.user:
            raise Http404("Interview not found")

        return interview

    def patch(self, request, interview_id):
        """Update interview status"""
        interview = self.get_object(request, interview_id)

        serializer = InterviewStatusUpdateSerializer(
            interview,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        # Use service layer to change status
        try:
            updated_interview = InterviewWorkflowService.change_status(
                interview,
                serializer.validated_data["status"],
                request.user
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = InterviewDetailSerializer(updated_interview)
        return Response(response_serializer.data)


class InterviewHistoryView(APIView):
    """
    Retrieve interview status history.

    GET /api/interviews/<id>/history/

    Authentication required.
    - Candidate: can view history of own interview only.
    - Recruiter: can view history only if they own the job.
    """

    permission_classes = (IsAuthenticated,)

    def get_object(self, request, interview_id):
        """Get interview with access control"""
        try:
            interview = Interview.objects.select_related(
                "application",
                "application__job",
                "application__candidate",
            ).get(id=interview_id)
        except Interview.DoesNotExist:
            raise Http404("Interview not found")

        # Candidate: can view own interview history
        if request.user.role == User.Roles.CANDIDATE:
            if interview.application.candidate != request.user:
                raise Http404("Interview not found")
            return interview

        # Recruiter: can view history only if job belongs to them
        if request.user.role == User.Roles.RECRUITER:
            if interview.application.job.recruiter != request.user:
                raise Http404("Interview not found")
            return interview

        # Everyone else: denied
        raise Http404("Interview not found")

    def get(self, request, interview_id):
        """Retrieve interview status history"""
        interview = self.get_object(request, interview_id)

        history = interview.status_history.select_related(
            "changed_by"
        ).order_by("changed_at")

        serializer = InterviewStatusHistorySerializer(history, many=True)
        return Response(serializer.data)
