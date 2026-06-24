from apps.applications.models import Application, ApplicationStatusHistory


class ApplicationWorkflowService:
    """Service layer for application workflow operations."""

    # Valid status transitions
    VALID_TRANSITIONS = {
        Application.ApplicationStatus.SUBMITTED: [
            Application.ApplicationStatus.UNDER_REVIEW,
        ],
        Application.ApplicationStatus.UNDER_REVIEW: [
            Application.ApplicationStatus.SHORTLISTED,
            Application.ApplicationStatus.REJECTED,
        ],
        Application.ApplicationStatus.SHORTLISTED: [
            Application.ApplicationStatus.HIRED,
            Application.ApplicationStatus.REJECTED,
        ],
        Application.ApplicationStatus.REJECTED: [],
        Application.ApplicationStatus.HIRED: [],
    }

    @classmethod
    def validate_transition(cls, old_status: str, new_status: str) -> bool:
        """
        Validate if a status transition is allowed.
        
        Args:
            old_status: Current status of the application
            new_status: Desired new status
            
        Returns:
            True if transition is valid, False otherwise
        """
        if old_status == new_status:
            return False
        
        allowed_transitions = cls.VALID_TRANSITIONS.get(old_status, [])
        return new_status in allowed_transitions

    @classmethod
    def change_status(cls, application: Application, new_status: str, changed_by) -> Application:
        """
        Change application status with validation.
        
        Args:
            application: Application instance to update
            new_status: New status to set
            changed_by: User who is making the change
            
        Returns:
            Updated application instance
            
        Raises:
            ValueError: If transition is invalid
        """
        old_status = application.status
        
        # Validate transition
        if not cls.validate_transition(old_status, new_status):
            raise ValueError("Invalid status transition.")
        
        # Update status
        application.status = new_status
        application.save(update_fields=["status", "updated_at"])
        
        # Create history record
        cls.create_history(application, old_status, new_status, changed_by)
        
        return application

    @classmethod
    def create_history(
        cls,
        application: Application,
        old_status: str,
        new_status: str,
        changed_by,
        notes: str = "",
    ) -> ApplicationStatusHistory:
        """
        Create a history record for status change.
        
        Args:
            application: Application instance
            old_status: Previous status
            new_status: New status
            changed_by: User who made the change
            notes: Optional notes for the change
            
        Returns:
            Created ApplicationStatusHistory instance
        """
        return ApplicationStatusHistory.objects.create(
            application=application,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            notes=notes,
        )
