from apps.notifications.models import Notification


class NotificationService:
    """Service layer for notification operations."""

    @classmethod
    def create_notification(
        cls,
        recipient,
        title: str,
        message: str,
        notification_type: str,
        metadata: dict = None,
    ) -> Notification:
        """
        Create a notification for a user.

        Args:
            recipient: User instance who will receive the notification
            title: Notification title
            message: Notification message
            notification_type: Type of notification (from Notification.NotificationType)
            metadata: Optional JSON-serializable metadata

        Returns:
            Created Notification instance
        """
        if metadata is None:
            metadata = {}

        return Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            metadata=metadata,
        )

    @classmethod
    def mark_as_read(cls, notification_id: str, user) -> Notification:
        """
        Mark a notification as read.

        Args:
            notification_id: UUID of the notification
            user: User requesting the mark as read (for ownership check)

        Returns:
            Updated Notification instance

        Raises:
            Notification.DoesNotExist: If notification doesn't exist or doesn't belong to user
        """
        notification = Notification.objects.get(id=notification_id, recipient=user)
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return notification

    @classmethod
    def mark_all_as_read(cls, user) -> int:
        """
        Mark all unread notifications for a user as read.

        Args:
            user: User whose notifications should be marked as read

        Returns:
            Number of notifications updated
        """
        count = Notification.objects.filter(recipient=user, is_read=False).update(
            is_read=True
        )
        return count

    @classmethod
    def notify_application_submitted(
        cls, recruiter, application_id: str, job_id: str, candidate_id: str
    ) -> Notification:
        """
        Notify recruiter when a candidate submits an application.

        Args:
            recruiter: Recruiter User instance
            application_id: UUID of the application
            job_id: UUID of the job
            candidate_id: UUID of the candidate

        Returns:
            Created Notification instance
        """
        return cls.create_notification(
            recipient=recruiter,
            title="New Application Received",
            message="A candidate has submitted an application for your job.",
            notification_type=Notification.NotificationType.APPLICATION_SUBMITTED,
            metadata={
                "application_id": application_id,
                "job_id": job_id,
                "candidate_id": candidate_id,
            },
        )

    @classmethod
    def notify_application_status_changed(
        cls,
        candidate,
        application_id: str,
        old_status: str,
        new_status: str,
    ) -> Notification:
        """
        Notify candidate when their application status changes.

        Args:
            candidate: Candidate User instance
            application_id: UUID of the application
            old_status: Previous status
            new_status: New status

        Returns:
            Created Notification instance
        """
        return cls.create_notification(
            recipient=candidate,
            title="Application Status Updated",
            message=f"Your application status has changed from {old_status} to {new_status}.",
            notification_type=Notification.NotificationType.APPLICATION_STATUS_CHANGED,
            metadata={
                "application_id": application_id,
                "old_status": old_status,
                "new_status": new_status,
            },
        )

    @classmethod
    def notify_interview_scheduled(
        cls, candidate, interview_id: str, application_id: str
    ) -> Notification:
        """
        Notify candidate when an interview is scheduled.

        Args:
            candidate: Candidate User instance
            interview_id: UUID of the interview
            application_id: UUID of the application

        Returns:
            Created Notification instance
        """
        return cls.create_notification(
            recipient=candidate,
            title="Interview Scheduled",
            message="An interview has been scheduled for your application.",
            notification_type=Notification.NotificationType.INTERVIEW_SCHEDULED,
            metadata={
                "interview_id": interview_id,
                "application_id": application_id,
            },
        )

    @classmethod
    def notify_interview_completed(
        cls, candidate, interview_id: str, application_id: str
    ) -> Notification:
        """
        Notify candidate when an interview is completed.

        Args:
            candidate: Candidate User instance
            interview_id: UUID of the interview
            application_id: UUID of the application

        Returns:
            Created Notification instance
        """
        return cls.create_notification(
            recipient=candidate,
            title="Interview Completed",
            message="Your interview has been completed.",
            notification_type=Notification.NotificationType.INTERVIEW_COMPLETED,
            metadata={
                "interview_id": interview_id,
                "application_id": application_id,
            },
        )

    @classmethod
    def notify_interview_cancelled(
        cls, candidate, interview_id: str, application_id: str
    ) -> Notification:
        """
        Notify candidate when an interview is cancelled.

        Args:
            candidate: Candidate User instance
            interview_id: UUID of the interview
            application_id: UUID of the application

        Returns:
            Created Notification instance
        """
        return cls.create_notification(
            recipient=candidate,
            title="Interview Cancelled",
            message="Your scheduled interview has been cancelled.",
            notification_type=Notification.NotificationType.INTERVIEW_CANCELLED,
            metadata={
                "interview_id": interview_id,
                "application_id": application_id,
            },
        )

    @classmethod
    def notify_match_created(cls, candidate, job_id: str, match_score: float) -> Notification:
        """
        Notify candidate when a new job match is created.

        Args:
            candidate: Candidate User instance
            job_id: UUID of the job
            match_score: Match score percentage

        Returns:
            Created Notification instance
        """
        return cls.create_notification(
            recipient=candidate,
            title="New Job Match",
            message=f"A new job matching your profile has been found with a match score of {match_score}%.",
            notification_type=Notification.NotificationType.MATCH_CREATED,
            metadata={
                "job_id": job_id,
                "match_score": match_score,
            },
        )
