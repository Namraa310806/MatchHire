from apps.interviews.models import Interview, InterviewStatusHistory
from apps.notifications.services.notification_service import NotificationService


class InterviewWorkflowService:
    """Service layer for interview workflow operations."""

    # Valid status transitions
    VALID_TRANSITIONS = {
        Interview.InterviewStatus.SCHEDULED: [
            Interview.InterviewStatus.COMPLETED,
            Interview.InterviewStatus.CANCELLED,
        ],
        Interview.InterviewStatus.COMPLETED: [],
        Interview.InterviewStatus.CANCELLED: [],
    }

    @classmethod
    def validate_transition(cls, old_status: str, new_status: str) -> bool:
        """
        Validate if a status transition is allowed.

        Args:
            old_status: Current status of the interview
            new_status: Desired new status

        Returns:
            True if transition is valid, False otherwise
        """
        if old_status == new_status:
            return False

        allowed_transitions = cls.VALID_TRANSITIONS.get(old_status, [])
        return new_status in allowed_transitions

    @classmethod
    def change_status(cls, interview: Interview, new_status: str, changed_by) -> Interview:
        """
        Change interview status with validation.

        Args:
            interview: Interview instance to update
            new_status: New status to set
            changed_by: User who is making the change

        Returns:
            Updated interview instance

        Raises:
            ValueError: If transition is invalid
        """
        old_status = interview.status

        # Validate transition
        if not cls.validate_transition(old_status, new_status):
            raise ValueError("Invalid status transition.")

        # Update status
        interview.status = new_status
        interview.save(update_fields=["status", "updated_at"])

        # Create history record
        cls.create_history(interview, old_status, new_status, changed_by)

        # Notify candidate about interview status change
        if new_status == Interview.InterviewStatus.COMPLETED:
            NotificationService.notify_interview_completed(
                candidate=interview.application.candidate,
                interview_id=str(interview.id),
                application_id=str(interview.application.id),
            )
        elif new_status == Interview.InterviewStatus.CANCELLED:
            NotificationService.notify_interview_cancelled(
                candidate=interview.application.candidate,
                interview_id=str(interview.id),
                application_id=str(interview.application.id),
            )

        return interview

    @classmethod
    def create_history(
        cls,
        interview: Interview,
        old_status: str,
        new_status: str,
        changed_by,
        notes: str = "",
    ) -> InterviewStatusHistory:
        """
        Create a history record for status change.

        Args:
            interview: Interview instance
            old_status: Previous status
            new_status: New status
            changed_by: User who made the change
            notes: Optional notes for the change

        Returns:
            Created InterviewStatusHistory instance
        """
        return InterviewStatusHistory.objects.create(
            interview=interview,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            notes=notes,
        )
