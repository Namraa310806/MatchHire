from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample

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
    CandidateProfileSerializer,
)
from .services.parser_service import ResumeParserService
from .services.versioning import ResumeVersioningService
from .services.extraction_service import ResumeExtractionService
from .services.search_service import ResumeSearchService
from matchhire_backend.core.validators import validate_uuid, validate_ordering, validate_search_length
from matchhire_backend.core.metrics import track_resume_upload

User = get_user_model()


class ResumeSearchPagination(PageNumberPagination):
    """Pagination for resume search results"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema(
	tags=["Resumes"],
	summary="Search resumes",
	description="Search and filter structured resume data. Authentication required. Recruiter only.",
	parameters=[
		OpenApiParameter(name='skill', description='Filter by skill name (can be multiple)', required=False, type=str),
		OpenApiParameter(name='location', description='Filter by location', required=False, type=str),
		OpenApiParameter(name='company', description='Filter by company name', required=False, type=str),
		OpenApiParameter(name='education', description='Filter by education degree or institution', required=False, type=str),
		OpenApiParameter(name='certification', description='Filter by certification name or issuer', required=False, type=str),
		OpenApiParameter(name='ordering', description='Order results (name, -name, created_at, -created_at)', required=False, type=str),
		OpenApiParameter(name='page', description='Page number', required=False, type=int),
		OpenApiParameter(name='page_size', description='Results per page (default: 20, max: 100)', required=False, type=int),
	],
	responses={
		200: OpenApiResponse(description="Resumes retrieved successfully with pagination."),
		403: OpenApiResponse(description="Only recruiters can search resumes.")
	}
)
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
    throttle_scope = 'authenticated'

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
        valid_ordering_fields = ['name', '-name', 'created_at', '-created_at']
        validate_ordering(ordering, valid_ordering_fields)
        
        # Validate search length
        for field in [location, company, education, certification]:
            if field:
                validate_search_length(field, max_length=200)

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


@extend_schema(
	tags=["Resumes"],
	summary="Upload resume",
	description="Upload a resume file (PDF or DOCX). Maximum file size: 10 MB. Authentication required. Candidate only.",
	request={
		"multipart/form-data": {
			"type": "object",
			"properties": {
				"file": {"type": "string", "format": "binary"}
			},
			"required": ["file"]
		}
	},
	responses={
		201: OpenApiResponse(description="Resume uploaded successfully."),
		400: OpenApiResponse(description="Invalid file type or size."),
		403: OpenApiResponse(description="Only candidates can upload resumes.")
	},
	examples=[
		OpenApiExample(
			"Resume upload",
			value={"file": "resume.pdf"},
			response_only=False,
		),
	]
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
    throttle_scope = 'resume_upload'

    def post(self, request):
        serializer = ResumeUploadSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        resume_version = serializer.save()

        # Track business metric
        try:
            track_resume_upload()
        except Exception:
            # Don't fail the request if metrics tracking fails
            pass

        response_serializer = ResumeVersionSerializer(resume_version)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
	tags=["Resumes"],
	summary="List my resumes",
	description="List all resumes for the current user. Authentication required. Candidate only.",
	responses={
		200: OpenApiResponse(description="Resumes retrieved successfully."),
		403: OpenApiResponse(description="Only candidates can view their resumes.")
	}
)
class ResumeListView(APIView):
    """
    List resumes for the current user.
    
    GET /api/resumes/
    
    Authentication required. Candidate only.
    Returns resumes ordered newest first.
    """
    permission_classes = (IsAuthenticated, IsCandidate)
    throttle_scope = 'authenticated'

    def get(self, request):
        """List all resumes for the current user"""
        # PERFORMANCE OPTIMIZATION: Use prefetch_related with Prefetch to fetch current versions
        # This eliminates N+1 queries in ResumeListSerializer.get_current_version()
        from django.db.models import Prefetch
        
        current_version_prefetch = Prefetch(
            'versions',
            queryset=ResumeVersion.objects.filter(is_current=True).select_related(
                'parsed_resume',
                'structured_resume'
            ),
            to_attr='current_version_prefetch'
        )
        
        resumes = Resume.objects.filter(
            user=request.user
        ).prefetch_related(
            current_version_prefetch
        ).order_by("-created_at")
        
        serializer = ResumeListSerializer(resumes, many=True)
        return Response(serializer.data)


@extend_schema(
	tags=["Resumes"],
	summary="Get resume details",
	description="Retrieve a specific resume. Authentication required. Candidate only.",
	responses={
		200: OpenApiResponse(description="Resume details retrieved successfully."),
		404: OpenApiResponse(description="Resume not found."),
		403: OpenApiResponse(description="Only candidates can view their resumes.")
	}
)
@extend_schema(
	tags=["Resumes"],
	summary="Delete resume",
	description="Delete a resume and all its versions. Authentication required. Candidate only.",
	responses={
		204: OpenApiResponse(description="Resume deleted successfully."),
		404: OpenApiResponse(description="Resume not found."),
		403: OpenApiResponse(description="Only candidates can delete their resumes.")
	}
)
class ResumeDetailView(APIView):
    """
    Retrieve a specific resume.
    
    GET /api/resumes/<id>/
    DELETE /api/resumes/<id>/
    
    Authentication required. Candidate only.
    Only owner can access their resumes.
    """
    permission_classes = (IsAuthenticated, IsCandidate)
    throttle_scope = 'authenticated'

    def get_object(self, request, id):
        """Get resume if owned by current user"""
        validate_uuid(id, "id")
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


@extend_schema(
	tags=["Resumes"],
	summary="Get active resume",
	description="Get the current resume with its current version. Authentication required. Candidate only.",
	responses={
		200: OpenApiResponse(description="Active resume retrieved successfully."),
		404: OpenApiResponse(description="No resume or current version found."),
		403: OpenApiResponse(description="Only candidates can access their resume.")
	}
)
class ActiveResumeView(APIView):
    """
    Get the current resume with its current version.

    GET /api/resumes/active/

    Authentication required. Candidate only.
    Returns 404 if no resume or current version exists.
    """
    permission_classes = (IsAuthenticated, IsCandidate)
    throttle_scope = 'authenticated'

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


@extend_schema(
	tags=["Resumes"],
	summary="Activate resume version",
	description="Activate a specific resume version. Authentication required. Candidate only.",
	responses={
		200: ResumeActivationSerializer,
		404: OpenApiResponse(description="Resume or version not found."),
		403: OpenApiResponse(description="Only candidates can activate their resume versions.")
	}
)
class ResumeActivateView(APIView):
    """
    Activate a specific resume version.

    PATCH /api/resumes/<id>/versions/<version_id>/activate/

    Authentication required. Candidate only.
    Transactional - deactivates current version and activates selected one.
    """
    permission_classes = (IsAuthenticated, IsCandidate)
    throttle_scope = 'authenticated'
    serializer_class = ResumeActivationSerializer

    def get_resume(self, request, id):
        """Get resume if owned by current user"""
        validate_uuid(id, "id")
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


@extend_schema(
	tags=["Resumes"],
	summary="Parse resume",
	description="Parse a resume to extract raw text. Authentication required. Candidate only.",
	request=None,
	responses={
		200: OpenApiResponse(description="Resume parsed successfully."),
		400: OpenApiResponse(description="Unsupported file type or corrupted file."),
		404: OpenApiResponse(description="Resume not found."),
		403: OpenApiResponse(description="Only candidates can parse their resumes.")
	}
)
class ParseResumeView(APIView):
    """
    Parse a resume to extract raw text.

    POST /api/resumes/<id>/parse/

    Authentication required. Candidate only.
    Only owner can parse their resumes.
    """
    permission_classes = (IsAuthenticated, IsCandidate)
    throttle_scope = 'resume_parsing'

    def get_object(self, request, id):
        """Get resume if owned by current user"""
        validate_uuid(id, "id")
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


@extend_schema(
	tags=["Resumes"],
	summary="Get parsed resume",
	description="Retrieve parsed resume information. Authentication required. Candidate only.",
	responses={
		200: OpenApiResponse(description="Parsed resume retrieved successfully."),
		404: OpenApiResponse(description="Resume or parsed resume not found."),
		403: OpenApiResponse(description="Only candidates can access their parsed resume.")
	}
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


@extend_schema(
	tags=["Resumes"],
	summary="Get resume version history",
	description="Get version history for a resume. Authentication required. Candidate only.",
	responses={
		200: OpenApiResponse(description="Version history retrieved successfully."),
		404: OpenApiResponse(description="Resume not found."),
		403: OpenApiResponse(description="Only candidates can access their resume history.")
	}
)
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


@extend_schema(
	tags=["Resumes"],
	summary="Get current resume version",
	description="Get the current version of a resume. Authentication required. Candidate only.",
	responses={
		200: OpenApiResponse(description="Current version retrieved successfully."),
		404: OpenApiResponse(description="Resume or current version not found."),
		403: OpenApiResponse(description="Only candidates can access their resume versions.")
	}
)
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


@extend_schema(
	tags=["Resumes"],
	summary="Rollback resume version",
	description="Rollback to a specific version of a resume. Authentication required. Candidate only.",
	request=None,
	responses={
		200: OpenApiResponse(description="Rollback successful."),
		404: OpenApiResponse(description="Resume or version not found."),
		403: OpenApiResponse(description="Only candidates can rollback their resume versions.")
	}
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


@extend_schema(
	tags=["Resumes"],
	summary="Parse resume version",
	description="Parse a specific resume version to extract raw text. Authentication required. Candidate only.",
	request=None,
	responses={
		200: OpenApiResponse(description="Resume version parsed successfully."),
		400: OpenApiResponse(description="Unsupported file type or corrupted file."),
		404: OpenApiResponse(description="Resume version not found."),
		403: OpenApiResponse(description="Only candidates can parse their resume versions.")
	}
)
class ParseResumeVersionView(APIView):
    """
    Parse a specific resume version to extract raw text.

    POST /api/resumes/versions/<version_id>/parse/

    Authentication required. Candidate only.
    Only owner can parse their resume versions.
    """
    permission_classes = (IsAuthenticated, IsCandidate)
    throttle_scope = 'resume_parsing'

    def get_object(self, request, version_id):
        """Get resume version if owned by current user"""
        validate_uuid(version_id, "version_id")
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


@extend_schema(
	tags=["Resumes"],
	summary="Get parsed resume version",
	description="Retrieve parsed resume information for a specific version. Authentication required. Candidate only.",
	responses={
		200: OpenApiResponse(description="Parsed resume version retrieved successfully."),
		404: OpenApiResponse(description="Resume version or parsed resume not found."),
		403: OpenApiResponse(description="Only candidates can access their parsed resume.")
	}
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


@extend_schema(
	tags=["Resumes"],
	summary="Extract structured resume data",
	description="Extract structured resume data from a parsed resume version. Authentication required. Candidate only.",
	request=None,
	responses={
		200: OpenApiResponse(description="Structured data extracted successfully."),
		400: OpenApiResponse(description="Resume must be successfully parsed before extraction."),
		404: OpenApiResponse(description="Resume version or parsed resume not found."),
		403: OpenApiResponse(description="Only candidates can extract structured data from their resume.")
	}
)
class ExtractResumeVersionView(APIView):
    """
    Extract structured resume data from a parsed resume version.

    POST /api/resumes/versions/<version_id>/extract/

    Authentication required. Candidate only.
    Only owner can extract structured data from their resume versions.
    """
    permission_classes = (IsAuthenticated, IsCandidate)
    throttle_scope = 'structured_extraction'

    def get_object(self, request, version_id):
        """Get parsed resume if owned by current user"""
        validate_uuid(version_id, "version_id")
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


@extend_schema(
	tags=["Resumes"],
	summary="Get structured resume data",
	description="Retrieve structured resume data for a specific version. Authentication required. Candidate only.",
	responses={
		200: OpenApiResponse(description="Structured resume data retrieved successfully."),
		404: OpenApiResponse(description="Resume version or structured resume not found."),
		403: OpenApiResponse(description="Only candidates can access their structured resume data.")
	}
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


@extend_schema(
	tags=["Resumes"],
	summary="Get candidate profile",
	description="Get candidate profile with structured resume data. Authentication required. Recruiter only.",
	responses={
		200: OpenApiResponse(description="Candidate profile retrieved successfully."),
		404: OpenApiResponse(description="Candidate or resume not found."),
		403: OpenApiResponse(description="Only recruiters can access candidate profiles.")
	}
)
class CandidateProfileView(APIView):
    """
    Get candidate profile with structured resume data.

    GET /api/candidates/<id>/

    Authentication required. Recruiter only.
    Returns candidate's current resume data including skills, experience, education, projects, certifications.
    """
    permission_classes = (IsAuthenticated, IsRecruiter)

    def get_object(self, request, candidate_id):
        """Get candidate's resume with access control"""
        try:
            candidate = User.objects.get(id=candidate_id, role=User.Roles.CANDIDATE)
        except User.DoesNotExist:
            raise Http404("Candidate not found")

        try:
            resume = Resume.objects.get(user=candidate)
        except Resume.DoesNotExist:
            raise Http404("Resume not found")

        return resume

    def get(self, request, candidate_id):
        """Get candidate profile"""
        resume = self.get_object(request, candidate_id)
        serializer = CandidateProfileSerializer(resume)
        return Response(serializer.data)


@extend_schema(
	tags=["Resumes"],
	summary="Search candidates",
	description="Search candidates with filters. Authentication required. Recruiter only.",
	parameters=[
		OpenApiParameter(name='skills', description='Filter by skill name (comma-separated)', required=False, type=str),
		OpenApiParameter(name='location', description='Filter by location', required=False, type=str),
		OpenApiParameter(name='experience_min', description='Minimum years of experience', required=False, type=float),
		OpenApiParameter(name='education', description='Filter by education level (bachelor, master, phd)', required=False, type=str),
		OpenApiParameter(name='match_score', description='Filter by minimum match score (requires job_id)', required=False, type=float),
		OpenApiParameter(name='job_id', description='Job ID for match score filtering', required=False, type=str),
	],
	responses={
		200: OpenApiResponse(description="Candidates retrieved successfully."),
		403: OpenApiResponse(description="Only recruiters can search candidates.")
	}
)
class CandidateSearchView(APIView):
    """
    Search candidates with filters.

    GET /api/candidates/search/

    Query parameters:
    - skills: Filter by skill name (comma-separated)
    - location: Filter by location
    - experience_min: Minimum years of experience
    - education: Filter by education level (bachelor, master, phd)
    - match_score: Filter by minimum match score (requires job_id)
    - job_id: Job ID for match score filtering

    Authentication required. Recruiter only.
    """
    permission_classes = (IsAuthenticated, IsRecruiter)

    def get(self, request):
        """Search candidates with filters"""
        # Get all candidates
        candidates = User.objects.filter(role=User.Roles.CANDIDATE)

        # Get resumes with structured data
        resumes = Resume.objects.filter(user__in=candidates)

        # Filter by skills
        skills = request.query_params.get("skills")
        if skills:
            skill_list = [s.strip() for s in skills.split(",")]
            # Get resumes that have current versions with matching skills
            resume_ids = Resume.objects.filter(
                versions__is_current=True,
                versions__structured_resume__skills__name__in=skill_list
            ).values_list("id", flat=True).distinct()
            resumes = resumes.filter(id__in=resume_ids)

        # Filter by location
        location = request.query_params.get("location")
        if location:
            resume_ids = Resume.objects.filter(
                versions__is_current=True,
                versions__structured_resume__location__icontains=location
            ).values_list("id", flat=True).distinct()
            resumes = resumes.filter(id__in=resume_ids)

        # Filter by experience (years)
        experience_min = request.query_params.get("experience_min")
        if experience_min:
            try:
                min_years = float(experience_min)
                # Filter candidates with at least min_years of experience
                # This requires calculating actual years from start_date/end_date
                # For now, we'll filter by experience count as a proxy
                # TODO: Implement actual years calculation in query
                pass
            except ValueError:
                return Response(
                    {"detail": "experience_min must be a number"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Filter by education level
        education = request.query_params.get("education")
        if education:
            education = education.lower()
            if education == "bachelor":
                resume_ids = Resume.objects.filter(
                    versions__is_current=True,
                    versions__structured_resume__education__degree__icontains="bachelor"
                ).values_list("id", flat=True).distinct()
                resumes = resumes.filter(id__in=resume_ids)
            elif education == "master":
                resume_ids = Resume.objects.filter(
                    versions__is_current=True,
                    versions__structured_resume__education__degree__icontains="master"
                ).values_list("id", flat=True).distinct()
                resumes = resumes.filter(id__in=resume_ids)
            elif education == "phd":
                resume_ids = Resume.objects.filter(
                    versions__is_current=True,
                    versions__structured_resume__education__degree__icontains="phd"
                ).values_list("id", flat=True).distinct()
                resumes = resumes.filter(id__in=resume_ids)

        # Filter by match score (requires job_id)
        job_id = request.query_params.get("job_id")
        match_score_min = request.query_params.get("match_score")
        if job_id and match_score_min:
            try:
                from apps.matching.models import JobMatch
                from apps.jobs.models import Job

                # Verify job ownership
                job = Job.objects.get(id=job_id, recruiter=request.user)

                try:
                    min_score = float(match_score_min)
                except ValueError:
                    return Response(
                        {"detail": "match_score must be a number"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Filter candidates by match score
                candidate_ids = JobMatch.objects.filter(
                    job=job,
                    match_score__gte=min_score
                ).values_list("candidate_id", flat=True)

                resumes = resumes.filter(user__in=candidate_ids)

            except Job.DoesNotExist:
                raise Http404("Job not found")

        # Serialize results
        serializer = CandidateProfileSerializer(resumes, many=True)
        return Response(serializer.data)

