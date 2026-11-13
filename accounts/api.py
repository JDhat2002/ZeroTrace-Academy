from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.access import has_membership, is_instructor


def _deny(detail):
    return Response({"detail": detail}, status=403)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pro_access(request):
    if not has_membership(request.user, "pro"):
        return _deny("This feature requires a Pro membership.")
    return Response({"detail": "Pro access granted.", "feature": "preview"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def elite_access(request):
    if not has_membership(request.user, "elite"):
        return _deny("This feature requires an Elite membership.")
    return Response({"detail": "Elite access granted.", "feature": "preview"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def instructor_access(request):
    if not is_instructor(request.user):
        return _deny("This feature requires an instructor account.")
    return Response({"detail": "Instructor access granted.", "feature": "preview"})
