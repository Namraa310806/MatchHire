from django.urls import path

from .views import (
    NotificationListView,
    MarkAsReadView,
    MarkAllAsReadView,
    UnreadCountView,
)

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
    path("<uuid:id>/read/", MarkAsReadView.as_view(), name="notification-mark-read"),
    path("read-all/", MarkAllAsReadView.as_view(), name="notification-mark-all-read"),
    path("unread-count/", UnreadCountView.as_view(), name="notification-unread-count"),
]
