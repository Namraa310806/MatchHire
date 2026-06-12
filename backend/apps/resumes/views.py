from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsCandidate
from .serializers import ResumeSerializer, ResumeUploadSerializer


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
        
        response_serializer = ResumeSerializer(resume)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )
