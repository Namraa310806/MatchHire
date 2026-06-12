from django.db import transaction
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsCandidate
from .models import Resume
from .serializers import (
    ResumeListSerializer,
    ResumeDetailSerializer,
    ResumeUploadSerializer,
    ResumeActivationSerializer,
)


class ResumeUploadView(APIView):
    """
    Upload a resume file.
    
    POST /api/resumes/upload/
    
    Authentication required. Candidate only.
    Multipart form-data with 'file' field.
    
    Supported file types: PDF, DOCX
    Maximum file size: 10 MB
    """
    permission_classes = (IsAuthenticated, IsCandidate)

    def post(self, request):
        serializer = ResumeUploadSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        resume = serializer.save()

        response_serializer = ResumeListSerializer(resume)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class ResumeListView(APIView):
    """
    List resumes for the current user.
    
    GET /api/resumes/
    
    Authentication required. Candidate only.
    Returns resumes ordered newest first.
    """
    permission_classes = (IsAuthenticated, IsCandidate)

    def get(self, request):
        """List all resumes for the current user"""
        resumes = Resume.objects.filter(user=request.user).order_by("-uploaded_at")
        serializer = ResumeListSerializer(resumes, many=True)
        return Response(serializer.data)


class ResumeDetailView(APIView):
    """
    Retrieve a specific resume.
    
    GET /api/resumes/<id>/
    DELETE /api/resumes/<id>/
    
    Authentication required. Candidate only.
    Only owner can access their resumes.
    """
    permission_classes = (IsAuthenticated, IsCandidate)

    def get_object(self, request, id):
        """Get resume if owned by current user"""
        try:
            return Resume.objects.get(id=id, user=request.user)
        except Resume.DoesNotExist:
            raise Http404("Resume not found")

    def get(self, request, id):
        """Retrieve resume details"""
        resume = self.get_object(request, id)
        serializer = ResumeDetailSerializer(resume)
        return Response(serializer.data)

    def delete(self, request, id):
        """Delete resume and its file"""
        from .services.storage import ResumeStorageService

        resume = self.get_object(request, id)

        # Delete file from storage
        ResumeStorageService.delete_resume_file(resume.file.name)

        # Delete database record
        resume.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class ActiveResumeView(APIView):
    """
    Get the current active resume.
    
    GET /api/resumes/active/
    
    Authentication required. Candidate only.
    Returns 404 if no active resume exists.
    """
    permission_classes = (IsAuthenticated, IsCandidate)

    def get(self, request):
        """Get the active resume for the current user"""
        try:
            active_resume = Resume.objects.get(user=request.user, is_active=True)
            serializer = ResumeDetailSerializer(active_resume)
            return Response(serializer.data)
        except Resume.DoesNotExist:
            return Response(
                {"detail": "No active resume found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class ResumeActivateView(APIView):
    """
    Activate a specific resume.
    
    PATCH /api/resumes/<id>/activate/
    
    Authentication required. Candidate only.
    Transactional - deactivates current active resume and activates selected one.
    """
    permission_classes = (IsAuthenticated, IsCandidate)

    def get_object(self, request, id):
        """Get resume if owned by current user"""
        try:
            return Resume.objects.get(id=id, user=request.user)
        except Resume.DoesNotExist:
            raise Http404("Resume not found")

    def patch(self, request, id):
        """Activate the specified resume"""
        resume = self.get_object(request, id)

        with transaction.atomic():
            # Deactivate all other resumes for this user
            Resume.objects.filter(user=request.user, is_active=True).update(
                is_active=False
            )

            # Activate the selected resume
            resume.is_active = True
            resume.save()

        serializer = ResumeActivationSerializer(resume)
        return Response(serializer.data)
