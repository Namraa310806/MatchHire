from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .permissions import IsCandidate, IsRecruiter, IsVerifiedUser


@extend_schema(
    tags=["Users"],
    summary="Candidate only endpoint",
    description="Test endpoint accessible only to candidates. Authentication required. Candidate only.",
    responses={
        200: OpenApiResponse(description="Access granted."),
        403: OpenApiResponse(description="Only candidates can access this endpoint."),
    },
)
@api_view(["GET"])
@permission_classes([IsCandidate])
def candidate_only_view(request):
    return Response({"message": "Access granted"})


@extend_schema(
    tags=["Users"],
    summary="Recruiter only endpoint",
    description="Test endpoint accessible only to recruiters. Authentication required. Recruiter only.",
    responses={
        200: OpenApiResponse(description="Access granted."),
        403: OpenApiResponse(description="Only recruiters can access this endpoint."),
    },
)
@api_view(["GET"])
@permission_classes([IsRecruiter])
def recruiter_only_view(request):
    return Response({"message": "Access granted"})


@extend_schema(
    tags=["Users"],
    summary="Verified user only endpoint",
    description="Test endpoint accessible only to verified users. Authentication required.",
    responses={
        200: OpenApiResponse(description="Access granted."),
        403: OpenApiResponse(
            description="Only verified users can access this endpoint."
        ),
    },
)
@api_view(["GET"])
@permission_classes([IsVerifiedUser])
def verified_only_view(request):
    return Response({"message": "Access granted"})
