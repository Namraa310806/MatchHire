from django.contrib.auth import get_user_model
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from apps.jobs.models import Job
from apps.matching.models import JobMatch
from apps.matching.services.matching import MatchingService
from apps.matching.serializers import (
    JobMatchSerializer,
    JobRecommendationSerializer,
    CandidateMatchSerializer,
)
from apps.core.cache import CacheService
from apps.users.permissions import IsCandidate, IsRecruiter

User = get_user_model()


@extend_schema(
    tags=["Matching"],
    summary="Calculate candidate-job match",
    description="Calculate or retrieve match between candidate and job. Authentication required. Candidate only.",
    responses={
        200: JobMatchSerializer,
        404: OpenApiResponse(description="Job not found or match not calculated."),
        403: OpenApiResponse(description="Only candidates can calculate matches."),
    },
)
class CandidateMatchView(APIView):
    """
    Calculate or retrieve match between candidate and job.

    POST /api/jobs/<job_id>/match/ - Calculate match
    GET /api/jobs/<job_id>/match/ - Retrieve existing match

    Authentication required. Candidate only.
    """

    permission_classes = (IsAuthenticated, IsCandidate)
    throttle_scope = "matching"
    serializer_class = JobMatchSerializer

    def get_object(self, request, job_id):
        """Get job with access control"""
        try:
            job = Job.objects.select_related("recruiter").get(id=job_id)
        except Job.DoesNotExist:
            raise Http404("Job not found")

        # Candidate can only match with ACTIVE jobs
        if job.status != Job.JobStatus.ACTIVE:
            raise Http404("Job not found")

        return job

    def post(self, request, job_id):
        """Calculate match between candidate and job"""
        job = self.get_object(request, job_id)

        # Calculate match using service
        job_match = MatchingService.calculate_match(request.user, job)

        serializer = JobMatchSerializer(job_match)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get(self, request, job_id):
        """Retrieve existing match"""
        job = self.get_object(request, job_id)

        try:
            job_match = JobMatch.objects.get(candidate=request.user, job=job)
        except JobMatch.DoesNotExist:
            return Response(
                {"detail": "Match not found. Calculate match first."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = JobMatchSerializer(job_match)
        return Response(serializer.data)


@extend_schema(
    tags=["Matching"],
    summary="Get job recommendations",
    description="Get job recommendations for candidate. Returns top 20 ACTIVE jobs ordered by match score DESC. Authentication required. Candidate only.",
    responses={
        200: OpenApiResponse(description="Job recommendations retrieved successfully."),
        403: OpenApiResponse(description="Only candidates can get recommendations."),
    },
)
class JobRecommendationsView(APIView):
    """
    Get job recommendations for candidate.

    GET /api/jobs/recommendations/

    Authentication required. Candidate only.
    Returns top 20 ACTIVE jobs ordered by match score DESC.
    """

    permission_classes = (IsAuthenticated, IsCandidate)
    throttle_scope = "matching"

    def get(self, request):
        """Get job recommendations for candidate"""
        # PERFORMANCE OPTIMIZATION: Use pre-calculated JobMatch records instead of calculating on-the-fly
        # This reduces query count from O(N) to O(1) where N is the number of active jobs
        # Additionally, cache the results for improved performance

        cache_key = CacheService.get_key("job_recommendations", str(request.user.id))

        def compute_recommendations():
            recommendations = (
                JobMatch.objects.filter(
                    candidate=request.user, job__status=Job.JobStatus.ACTIVE
                )
                .select_related("job", "job__recruiter")
                .order_by("-match_score", "-calculated_at")[:20]
            )

            serializer = JobRecommendationSerializer(recommendations, many=True)
            return serializer.data

        data = CacheService.get_or_set(
            cache_key,
            compute_recommendations,
            ttl=CacheService.TTL_CONFIG["job_recommendations"],
        )

        return Response(data)


@extend_schema(
    tags=["Matching"],
    summary="Get matching candidates",
    description="Get matching candidates for recruiter's job. Returns candidates ordered by match score DESC. Authentication required. Recruiter only.",
    parameters=[
        OpenApiParameter(
            name="job_id", description="Job ID for matching", required=True, type=str
        ),
    ],
    responses={
        200: OpenApiResponse(description="Matching candidates retrieved successfully."),
        400: OpenApiResponse(description="job_id query parameter is required."),
        403: OpenApiResponse(
            description="Only recruiters can get matching candidates."
        ),
        404: OpenApiResponse(description="Job not found."),
    },
)
class RecruiterCandidatesView(APIView):
    """
    Get matching candidates for recruiter's job.

    GET /api/recruiter/candidates/?job_id=<uuid>

    Authentication required. Recruiter only.
    Returns top matching candidates for the job ordered by match score DESC.
    """

    permission_classes = (IsAuthenticated, IsRecruiter)
    throttle_scope = "matching"

    def get(self, request):
        """Get matching candidates for recruiter's job"""
        job_id = request.query_params.get("job_id")

        if not job_id:
            return Response(
                {"detail": "job_id query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify job ownership
        try:
            job = Job.objects.get(id=job_id, recruiter=request.user)
        except Job.DoesNotExist:
            raise Http404("Job not found")

        # PERFORMANCE OPTIMIZATION: Use pre-calculated JobMatch records instead of calculating on-the-fly
        # This reduces query count from O(N) to O(1) where N is the number of candidates
        candidate_matches = (
            JobMatch.objects.filter(job=job)
            .select_related("candidate")
            .order_by("-match_score", "-calculated_at")
        )

        serializer = CandidateMatchSerializer(candidate_matches, many=True)
        return Response(serializer.data)
