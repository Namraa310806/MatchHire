from django.http import Http404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer
from .services.notification_service import NotificationService


class NotificationPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100


class NotificationListView(APIView):
    """
    List notifications for the authenticated user.

    GET /api/notifications/

    Authentication required.
    Returns only notifications belonging to request.user.
    Ordered newest first.
    Paginated (20 per page, max 100).
    """
    permission_classes = (IsAuthenticated,)
    pagination_class = NotificationPagination
    throttle_scope = 'notification'

    def get(self, request):
        """List all notifications for the current user"""
        notifications = Notification.objects.filter(
            recipient=request.user
        ).select_related("recipient").order_by("-created_at")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(notifications, request)
        serializer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class MarkAsReadView(APIView):
    """
    Mark a notification as read.

    PATCH /api/notifications/<id>/read/

    Authentication required. Owner only.
    """
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'notification'

    def get_object(self, request, id):
        """Get notification if owned by current user"""
        try:
            notification = Notification.objects.get(id=id, recipient=request.user)
        except Notification.DoesNotExist:
            raise Http404("Notification not found")
        return notification

    def patch(self, request, id):
        """Mark notification as read"""
        notification = self.get_object(request, id)
        updated_notification = NotificationService.mark_as_read(id, request.user)
        serializer = NotificationSerializer(updated_notification)
        return Response(serializer.data)


class MarkAllAsReadView(APIView):
    """
    Mark all notifications as read for the authenticated user.

    POST /api/notifications/read-all/

    Authentication required.
    """
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'notification'

    def post(self, request):
        """Mark all unread notifications as read"""
        updated_count = NotificationService.mark_all_as_read(request.user)
        return Response({"updated_count": updated_count})


class UnreadCountView(APIView):
    """
    Get unread notification count for the authenticated user.

    GET /api/notifications/unread-count/

    Authentication required.
    """
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'notification'

    def get(self, request):
        """Get unread notification count"""
        unread_count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        return Response({"unread_count": unread_count})
