from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce

from apps.admin.models import ModerationLog
from apps.applications.models import Application
from apps.interviews.models import Interview
from apps.jobs.models import Job
from apps.notifications.models import Notification
from apps.resumes.models import Resume
from apps.users.models import User


class AdminModerationService:
    """Service layer for all admin moderation operations."""

    @staticmethod
    def update_user(user_id, is_active=None, role=None, admin_user=None, reason=""):
        """Update user with moderation logging."""
        user = User.objects.get(id=user_id)
        
        old_is_active = user.is_active
        old_role = user.role
        
        if is_active is not None:
            user.is_active = is_active
        if role is not None:
            user.role = role
        
        user.save()
        
        # Determine action type
        action = ModerationLog.ActionType.UPDATE
        if is_active is not None:
            if is_active and not old_is_active:
                action = ModerationLog.ActionType.ENABLE
            elif not is_active and old_is_active:
                action = ModerationLog.ActionType.DISABLE
        
        # Create moderation log
        AdminModerationService.create_log(
            admin=admin_user,
            action=action,
            resource_type=ModerationLog.ResourceType.USER,
            resource_id=user_id,
            reason=reason,
            metadata={
                "old_is_active": old_is_active,
                "new_is_active": user.is_active,
                "old_role": old_role,
                "new_role": user.role,
            },
        )
        
        return user

    @staticmethod
    def update_job(job_id, status=None, admin_user=None, reason=""):
        """Update job status with moderation logging."""
        job = Job.objects.get(id=job_id)
        
        old_status = job.status
        
        if status is not None:
            job.status = status
            job.save()
        
        # Create moderation log
        AdminModerationService.create_log(
            admin=admin_user,
            action=ModerationLog.ActionType.STATUS_CHANGE,
            resource_type=ModerationLog.ResourceType.JOB,
            resource_id=job_id,
            reason=reason,
            metadata={
                "old_status": old_status,
                "new_status": job.status,
            },
        )
        
        return job

    @staticmethod
    def update_resume(resume_id, is_active=None, admin_user=None, reason=""):
        """Update resume with moderation logging."""
        resume = Resume.objects.get(id=resume_id)
        
        old_is_active = resume.user.is_active
        
        if is_active is not None:
            resume.user.is_active = is_active
            resume.user.save()
        
        # Determine action type
        action = ModerationLog.ActionType.UPDATE
        if is_active is not None:
            if is_active and not old_is_active:
                action = ModerationLog.ActionType.ENABLE
            elif not is_active and old_is_active:
                action = ModerationLog.ActionType.DISABLE
        
        # Create moderation log
        AdminModerationService.create_log(
            admin=admin_user,
            action=action,
            resource_type=ModerationLog.ResourceType.RESUME,
            resource_id=resume_id,
            reason=reason,
            metadata={
                "old_is_active": old_is_active,
                "new_is_active": resume.user.is_active,
            },
        )
        
        return resume

    @staticmethod
    def create_log(admin, action, resource_type, resource_id, reason="", metadata=None):
        """Create a moderation log entry."""
        if metadata is None:
            metadata = {}
        
        ModerationLog.objects.create(
            admin=admin,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            reason=reason,
            metadata=metadata,
        )

    @staticmethod
    def dashboard():
        """Get platform statistics using aggregate queries."""
        stats = User.objects.aggregate(
            total_users=Count("id"),
            total_candidates=Count("id", filter=Q(role=User.Roles.CANDIDATE)),
            total_recruiters=Count("id", filter=Q(role=User.Roles.RECRUITER)),
            active_users=Count("id", filter=Q(is_active=True)),
            inactive_users=Count("id", filter=Q(is_active=False)),
        )
        
        job_stats = Job.objects.aggregate(
            total_jobs=Count("id"),
            active_jobs=Count("id", filter=Q(status=Job.JobStatus.ACTIVE)),
            draft_jobs=Count("id", filter=Q(status=Job.JobStatus.DRAFT)),
            closed_jobs=Count("id", filter=Q(status=Job.JobStatus.CLOSED)),
        )
        
        resume_stats = Resume.objects.aggregate(
            total_resumes=Count("id"),
        )
        
        application_stats = Application.objects.aggregate(
            total_applications=Count("id"),
        )
        
        interview_stats = Interview.objects.aggregate(
            total_interviews=Count("id"),
        )
        
        notification_stats = Notification.objects.aggregate(
            total_notifications=Count("id"),
        )
        
        return {
            **stats,
            **job_stats,
            **resume_stats,
            **application_stats,
            **interview_stats,
            **notification_stats,
        }
