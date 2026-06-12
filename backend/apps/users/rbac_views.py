from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .permissions import IsCandidate, IsRecruiter, IsVerifiedUser


@api_view(["GET"])
@permission_classes([IsCandidate])
def candidate_only_view(request):
    return Response({"message": "Access granted"})


@api_view(["GET"])
@permission_classes([IsRecruiter])
def recruiter_only_view(request):
    return Response({"message": "Access granted"})


@api_view(["GET"])
@permission_classes([IsVerifiedUser])
def verified_only_view(request):
    return Response({"message": "Access granted"})
