from django.db import transaction
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from apps.users.permissions import IsCandidate, IsRecruiter
from .models import Resume, ParsedResume, ResumeVersion, StructuredResume
from .parsers import UnsupportedResumeType, CorruptedResumeError
from .serializers import (
    ResumeListSerializer,
    ResumeDetailSerializer,
    ResumeUploadSerializer,
    ResumeActivationSerializer,
    ParsedResumeSerializer,
    ParseResumeResponseSerializer,
    ResumeVersionSerializer,
    RollbackResponseSerializer,
    StructuredResumeSerializer,
    ExtractResumeResponseSerializer,
    ResumeSearchResultSerializer,
)
from .services.parser_service import ResumeParserService
from .services.versioning import ResumeVersioningService
from .services.extraction_service import ResumeExtractionService
from .services.search_service import ResumeSearchService


class ResumeSearchPagination(PageNumberPagination):
    """Pagination for resume search results"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ResumeSearchView(APIView):
    """
    Search and filter structured resume data.
    
    GET /api/resumes/search/
    
    Authentication required. Recruiter only.
    
    Query parameters:
    - skill: Filter by skill name (can be multiple)
    - location: Filter by location
    - company: Filter by company name
    - education: Filter by education degree or institution
    - certification: Filter by certification name or issuer
    - ordering: Order results (name, -name, created_at, -created_at)
    - page: Page number
    - page_size: Results per page (default: 20, max: 100)
    
    Example:
    /api/resumes/search/?skill=Python&skill=Django&location=Ahmedabad&ordering=name
    """
    permission_classes = (IsAuthenticated, IsRecruiter)
    pagination_class = ResumeSearchPagination

    def get(self, request):
        """Search resumes with filters"""
        # Extract query parameters
        skills = request.query_params.getlist('skill', None)
        location = request.query_params.get('location', None)
        company = request.query_params.get('company', None)
        education = request.query_params.get('education', None)
        certification = request.query_params.get('certification', None)
        ordering = request.query_params.get('ordering', None)

        # Validate ordering
        if ordering and not ResumeSearchService.validate_ordering(ordering):
            return Response(
                {"detail": f"Invalid ordering field: {ordering}. Valid fields: name, -name, created_at, -created_at"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Perform search
        queryset = ResumeSearchService.search(
            skills=skills if skills else None,
            location=location,
            company=company,
            education=education,
            certification=certification,
            ordering=ordering,
        )

        # Paginate results
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = ResumeSearchResultSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # Fallback if pagination is not applied
        serializer = ResumeSearchResultSerializer(queryset, many=True)
        return Response(serializer.data)


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
        resume_version = serializer.save()

        response_serializer = ResumeVersionSerializer(resume_version)
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
        resumes = Resume.objects.filter(user=request.user).order_by("-created_at")
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
        """Delete resume and all its versions"""
        from .services.storage import ResumeStorageService

        resume = self.get_object(request, id)

        # Delete all version files from storage
        for version in resume.versions.all():
            ResumeStorageService.delete_resume_file(version.file.name)

        # Delete database record (cascade deletes versions)
        resume.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class ActiveResumeView(APIView):
    """
    Get the current resume with its current version.
    
    GET /api/resumes/active/
    
    Authentication required. Candidate only.
    Returns 404 if no resume or current version exists.
    """
    permission_classes = (IsAuthenticated, IsCandidate)

    def get(self, request):
        """Get the resume with current version for the current user"""
        try:
            resume = Resume.objects.get(user=request.user)
            serializer = ResumeDetailSerializer(resume)
            return Response(serializer.data)
        except Resume.DoesNotExist:
            return Response(
                {"detail": "No resume found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class ResumeActivateView(APIView):
    """
    Activate a specific resume version.
    
    PATCH /api/resumes/<id>/versions/<version_id>/activate/
    
    Authentication required. Candidate only.
    Transactional - deactivates current version and activates selected one.
    """
    permission_classes = (IsAuthenticated, IsCandidate)

    def get_resume(self, request, id):
        """Get resume if owned by current user"""
        try:
            return Resume.objects.get(id=id, user=request.user)
        except Resume.DoesNotExist:
            raise Http404("Resume not found")

    def patch(self, request, id, version_id):
        """Activate the specified version"""
        resume = self.get_resume(request, id)

        try:
            # Perform rollback to activate the version
            current_version = ResumeVersioningService.rollback_version(
                resume, version_id
            )

            serializer = ResumeActivationSerializer(resume)
            return Response(serializer.data)

        except ResumeVersion.DoesNotExist:
            return Response(
                {"detail": "Version not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class ParseResumeView(APIView):
    """
    Parse a resume to extract raw text.
    
    POST /api/resumes/<id>/parse/
    
    Authentication required. Candidate only.
    Only owner can parse their resumes.
    """
    permission_classes = (IsAuthenticated, IsCandidate)

    def get_object(self, request, id):
        """Get resume if owned by current user"""
        try:
            return Resume.objects.select_related("user").get(id=id, user=request.user)
        except Resume.DoesNotExist:
            raise Http404("Resume not found")

    def post(self, request, id):
        """Parse the current version of the specified resume"""
        resume = self.get_object(request, id)

        try:
            # Get the current version
            resume_version = ResumeVersioningService.get_current_version(resume)

            # Parse the resume version
            parsed_resume = ResumeParserService.parse_resume_version(resume_version)

            # Return response
            response_data = {
                "resume_version_id": str(parsed_resume.resume_version.id),
                "resume_id": str(parsed_resume.resume_version.resume.id),
                "status": parsed_resume.status,
                "text_length": len(parsed_resume.raw_text) if parsed_resume.raw_text else 0,
            }
            serializer = ParseResumeResponseSerializer(response_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ResumeVersion.DoesNotExist:
            return Response(
                {"detail": "No current version found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except UnsupportedResumeType as e:
            # Mark as failed and return error
            ResumeParserService.mark_as_failed(resume_version, str(e))
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except CorruptedResumeError as e:
            # Mark as failed and return error
            ResumeParserService.mark_as_failed(resume_version, str(e))
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            # Mark as failed and return error
            ResumeParserService.mark_as_failed(resume_version, str(e))
            return Response(
                {"detail": "Failed to parse resume"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ParsedResumeDetailView(APIView):
    """
    Retrieve parsed resume information.
    
    GET /api/resumes/<id>/parsed/
    
    Authentication required. Candidate only.
    Only owner can access their parsed resume data.
    Does NOT return full raw text.
    """
    permission_classes = (IsAuthenticated, IsCandidate)

    def get_object(self, request, id):
        """Get parsed resume if owned by current user"""
        try:
            resume = Resume.objects.get(id=id, user=request.user)
            resume_version = ResumeVersioningService.get_current_version(resume)
            return ParsedResume.objects.select_related("resume_version").get(resume_version=resume_version)
        except Resume.DoesNotExist:
            raise Http404("Resume not found")
        except ResumeVersion.DoesNotExist:
            raise Http404("No current version found")
        except ParsedResume.DoesNotExist:
            raise Http404("Parsed resume not found")

    def get(self, request, id):
        """Retrieve parsed resume details"""
        parsed_resume = self.get_object(request, id)
        serializer = ParsedResumeSerializer(parsed_resume)
        return Response(serializer.data)


class ResumeVersionHistoryView(APIView):
    """
    Get version history for a resume.
    
    GET /api/resumes/<id>/versions/
    
    Authentication required. Candidate only.
    Returns versions ordered newest first.
    """
    permission_classes = (IsAuthenticated, IsCandidate)

    def get_object(self, request, id):
        """Get resume if owned by current user"""
        try:
            return Resume.objects.get(id=id, user=request.user)
        except Resume.DoesNotExist:
            raise Http404("Resume not found")

    def get(self, request, id):
        """Get version history for the resume"""
        resume = self.get_object(request, id)
        
        # Get version history with optimization
        versions = ResumeVersion.objects.filter(resume=resume).select_related(
            "parsed_resume"
        ).order_by("-version_number")
        
        serializer = ResumeVersionSerializer(versions, many=True)
        return Response(serializer.data)


class CurrentResumeVersionView(APIView):
    """
    Get the current version of a resume.
    
    GET /api/resumes/<id>/versions/current/
    
    Authentication required. Candidate only.
    Returns 404 if no current version exists.
    """
    permission_classes = (IsAuthenticated, IsCandidate)

    def get_object(self, request, id):
        """Get resume if owned by current user"""
        try:
            return Resume.objects.get(id=id, user=request.user)
        except Resume.DoesNotExist:
            raise Http404("Resume not found")

    def get(self, request, id):
        """Get the current version of the resume"""
        resume = self.get_object(request, id)
        
        try:
            current_version = ResumeVersion.objects.filter(
                resume=resume, is_current=True
            ).select_related("parsed_resume").get()
            
            serializer = ResumeVersionSerializer(current_version)
            return Response(serializer.data)
        except ResumeVersion.DoesNotExist:
            return Response(
                {"detail": "No current version found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class RollbackResumeVersionView(APIView):
    """
    Rollback to a specific version of a resume.

    POST /api/resumes/<id>/versions/<version_id>/rollback/

    Authentication required. Candidate only.
    Transactional - deactivates current version and activates selected one.
    """
    permission_classes = (IsAuthenticated, IsCandidate)

    def get_resume(self, request, id):
        """Get resume if owned by current user"""
        try:
            return Resume.objects.get(id=id, user=request.user)
        except Resume.DoesNotExist:
            raise Http404("Resume not found")

    def post(self, request, id, version_id):
        """Rollback to the specified version"""
        resume = self.get_resume(request, id)

        try:
            # Perform rollback
            current_version = ResumeVersioningService.rollback_version(
                resume, version_id
            )

            # Return response
            response_data = {
                "resume_id": str(resume.id),
                "current_version": current_version.version_number,
            }
            serializer = RollbackResponseSerializer(response_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ResumeVersion.DoesNotExist:
            return Response(
                {"detail": "Version not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class ParseResumeVersionView(APIView):
    """
    Parse a specific resume version to extract raw text.

    POST /api/resumes/versions/<version_id>/parse/

    Authentication required. Candidate only.
    Only owner can parse their resume versions.
    """
    permission_classes = (IsAuthenticated, IsCandidate)

    def get_object(self, request, version_id):
        """Get resume version if owned by current user"""
        try:
            return ResumeVersion.objects.select_related("resume").get(
                id=version_id, resume__user=request.user
            )
        except ResumeVersion.DoesNotExist:
            raise Http404("Resume version not found")

    def post(self, request, version_id):
        """Parse the specified resume version"""
        resume_version = self.get_object(request, version_id)

        try:
            # Parse the resume version
            parsed_resume = ResumeParserService.parse_resume_version(resume_version)

            # Return response
            response_data = {
                "resume_version_id": str(parsed_resume.resume_version.id),
                "resume_id": str(parsed_resume.resume_version.resume.id),
                "status": parsed_resume.status,
                "text_length": len(parsed_resume.raw_text) if parsed_resume.raw_text else 0,
            }
            serializer = ParseResumeResponseSerializer(response_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except UnsupportedResumeType as e:
            # Mark as failed and return error
            ResumeParserService.mark_as_failed(resume_version, str(e))
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except CorruptedResumeError as e:
            # Mark as failed and return error
            ResumeParserService.mark_as_failed(resume_version, str(e))
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            # Mark as failed and return error
            ResumeParserService.mark_as_failed(resume_version, str(e))
            return Response(
                {"detail": "Failed to parse resume"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ParsedResumeVersionDetailView(APIView):
    """
    Retrieve parsed resume information for a specific version.

    GET /api/resumes/versions/<version_id>/parsed/

    Authentication required. Candidate only.
    Only owner can access their parsed resume data.
    Does NOT return full raw text.
    """
    permission_classes = (IsAuthenticated, IsCandidate)

    def get_object(self, request, version_id):
        """Get parsed resume if owned by current user"""
        try:
            resume_version = ResumeVersion.objects.select_related("resume").get(
                id=version_id, resume__user=request.user
            )
            return ParsedResume.objects.select_related("resume_version").get(
                resume_version=resume_version
            )
        except ResumeVersion.DoesNotExist:
            raise Http404("Resume version not found")
        except ParsedResume.DoesNotExist:
            raise Http404("Parsed resume not found")

    def get(self, request, version_id):
        """Retrieve parsed resume details"""
        parsed_resume = self.get_object(request, version_id)
        serializer = ParsedResumeSerializer(parsed_resume)
        return Response(serializer.data)


class ExtractResumeVersionView(APIView):
    """
    Extract structured resume data from a parsed resume version.

    POST /api/resumes/versions/<version_id>/extract/

    Authentication required. Candidate only.
    Only owner can extract structured data from their resume versions.
    """
    permission_classes = (IsAuthenticated, IsCandidate)

    def get_object(self, request, version_id):
        """Get parsed resume if owned by current user"""
        try:
            resume_version = ResumeVersion.objects.select_related("resume").get(
                id=version_id, resume__user=request.user
            )
            return ParsedResume.objects.select_related("resume_version").get(
                resume_version=resume_version
            )
        except ResumeVersion.DoesNotExist:
            raise Http404("Resume version not found")
        except ParsedResume.DoesNotExist:
            raise Http404("Parsed resume not found")

    def post(self, request, version_id):
        """Extract structured data from the parsed resume version"""
        parsed_resume = self.get_object(request, version_id)

        if parsed_resume.status != ParsedResume.ParseStatus.SUCCESS:
            return Response(
                {"detail": "Resume must be successfully parsed before extraction."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Extract structured data
            structured_resume = ResumeExtractionService.extract(parsed_resume)

            # Return response
            response_data = {
                "structured_resume_id": str(structured_resume.id),
                "resume_version_id": str(structured_resume.resume_version.id),
                "resume_id": str(structured_resume.resume_version.resume.id),
                "status": "success",
            }
            serializer = ExtractResumeResponseSerializer(response_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"detail": "Failed to extract structured resume data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class StructuredResumeVersionView(APIView):
    """
    Retrieve structured resume data for a specific version.

    GET /api/resumes/versions/<version_id>/structured/

    Authentication required. Candidate only.
    Only owner can access their structured resume data.
    """
    permission_classes = (IsAuthenticated, IsCandidate)

    def get_object(self, request, version_id):
        """Get structured resume if owned by current user"""
        try:
            resume_version = ResumeVersion.objects.select_related("resume").get(
                id=version_id, resume__user=request.user
            )
            return StructuredResume.objects.select_related("resume_version").get(
                resume_version=resume_version
            )
        except ResumeVersion.DoesNotExist:
            raise Http404("Resume version not found")
        except StructuredResume.DoesNotExist:
            raise Http404("Structured resume not found")

    def get(self, request, version_id):
        """Retrieve structured resume details"""
        structured_resume = self.get_object(request, version_id)
        serializer = StructuredResumeSerializer(structured_resume)
        return Response(serializer.data)
