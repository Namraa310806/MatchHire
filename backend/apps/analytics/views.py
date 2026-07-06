from django.db.models import Count, Q, Avg
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.models import Application
from apps.interviews.models import Interview
from apps.jobs.models import Job
from apps.jobs.permissions import IsJobOwner
from apps.matching.models import JobMatch
from apps.users.permissions import IsCandidate, IsRecruiter

from .serializers import (
    RecruiterDashboardSerializer,
    CandidateDashboardSerializer,
    JobAnalyticsSerializer,
    TopCandidateSerializer,
)

# Constants for dashboard limits
TOP_CANDIDATES_LIMIT = 20


class RecruiterDashboardView(APIView):
    """
    Recruiter dashboard analytics.
    
    GET /api/analytics/recruiter/dashboard/
    
    Authentication required. Recruiter only.
    Returns aggregated metrics for the recruiter's jobs, applications, and interviews.
    """
    permission_classes = (IsAuthenticated, IsRecruiter)
    throttle_scope = 'analytics'

    def get(self, request):
        """Get recruiter dashboard analytics with query optimization"""
        recruiter = request.user
        
        # Get job metrics in a single query
        job_metrics = Job.objects.filter(recruiter=recruiter).aggregate(
            total_jobs=Count('id'),
            active_jobs=Count('id', filter=Q(status=Job.JobStatus.ACTIVE)),
            closed_jobs=Count('id', filter=Q(status=Job.JobStatus.CLOSED)),
        )
        
        # Get application metrics in a single query
        # Filter applications for jobs owned by this recruiter
        application_metrics = Application.objects.filter(
            job__recruiter=recruiter
        ).aggregate(
            total_applications=Count('id'),
            submitted_applications=Count('id', filter=Q(status=Application.ApplicationStatus.SUBMITTED)),
            under_review_applications=Count('id', filter=Q(status=Application.ApplicationStatus.UNDER_REVIEW)),
            shortlisted_applications=Count('id', filter=Q(status=Application.ApplicationStatus.SHORTLISTED)),
            rejected_applications=Count('id', filter=Q(status=Application.ApplicationStatus.REJECTED)),
            hired_applications=Count('id', filter=Q(status=Application.ApplicationStatus.HIRED)),
        )
        
        # Get interview metrics in a single query
        # Filter interviews for applications on jobs owned by this recruiter
        interview_metrics = Interview.objects.filter(
            application__job__recruiter=recruiter
        ).aggregate(
            scheduled_interviews=Count('id', filter=Q(status=Interview.InterviewStatus.SCHEDULED)),
            completed_interviews=Count('id', filter=Q(status=Interview.InterviewStatus.COMPLETED)),
            cancelled_interviews=Count('id', filter=Q(status=Interview.InterviewStatus.CANCELLED)),
        )
        
        # Combine all metrics
        data = {
            **job_metrics,
            **application_metrics,
            **interview_metrics,
        }
        
        serializer = RecruiterDashboardSerializer(data)
        return Response(serializer.data)


class CandidateDashboardView(APIView):
    """
    Candidate dashboard analytics.
    
    GET /api/analytics/candidate/dashboard/
    
    Authentication required. Candidate only.
    Returns aggregated metrics for the candidate's applications, interviews, and matches.
    """
    permission_classes = (IsAuthenticated, IsCandidate)
    throttle_scope = 'analytics'

    def get(self, request):
        """Get candidate dashboard analytics with query optimization"""
        candidate = request.user
        
        # Get application metrics in a single query
        application_metrics = Application.objects.filter(
            candidate=candidate
        ).aggregate(
            total_applications=Count('id'),
            submitted=Count('id', filter=Q(status=Application.ApplicationStatus.SUBMITTED)),
            under_review=Count('id', filter=Q(status=Application.ApplicationStatus.UNDER_REVIEW)),
            shortlisted=Count('id', filter=Q(status=Application.ApplicationStatus.SHORTLISTED)),
            rejected=Count('id', filter=Q(status=Application.ApplicationStatus.REJECTED)),
            hired=Count('id', filter=Q(status=Application.ApplicationStatus.HIRED)),
        )
        
        # Get interview metrics in a single query
        interview_metrics = Interview.objects.filter(
            application__candidate=candidate
        ).aggregate(
            scheduled_interviews=Count('id', filter=Q(status=Interview.InterviewStatus.SCHEDULED)),
            completed_interviews=Count('id', filter=Q(status=Interview.InterviewStatus.COMPLETED)),
            cancelled_interviews=Count('id', filter=Q(status=Interview.InterviewStatus.CANCELLED)),
        )
        
        # Get match metrics in a single query
        match_metrics = JobMatch.objects.filter(
            candidate=candidate
        ).aggregate(
            total_matches=Count('id'),
            average_match_score=Avg('match_score'),
        )
        
        # Combine all metrics
        data = {
            **application_metrics,
            **interview_metrics,
            **match_metrics,
        }
        
        # Handle None values for average_match_score when no matches exist
        if data['average_match_score'] is None:
            data['average_match_score'] = 0.0
        
        serializer = CandidateDashboardSerializer(data)
        return Response(serializer.data)


class JobAnalyticsView(APIView):
    """
    Job-specific analytics for recruiters.
    
    GET /api/analytics/recruiter/jobs/<job_id>/
    
    Authentication required. Recruiter owner only.
    Returns application metrics and conversion rate for a specific job.
    """
    permission_classes = (IsAuthenticated, IsRecruiter, IsJobOwner)
    throttle_scope = 'analytics'

    def get_object(self, request, job_id):
        """Get job if owned by current recruiter"""
        try:
            return Job.objects.get(id=job_id, recruiter=request.user)
        except Job.DoesNotExist:
            raise Http404("Job not found")

    def get(self, request, job_id):
        """Get job analytics with query optimization"""
        job = self.get_object(request, job_id)
        
        # Get application metrics in a single query
        application_metrics = Application.objects.filter(
            job=job
        ).aggregate(
            total_applications=Count('id'),
            submitted=Count('id', filter=Q(status=Application.ApplicationStatus.SUBMITTED)),
            under_review=Count('id', filter=Q(status=Application.ApplicationStatus.UNDER_REVIEW)),
            shortlisted=Count('id', filter=Q(status=Application.ApplicationStatus.SHORTLISTED)),
            rejected=Count('id', filter=Q(status=Application.ApplicationStatus.REJECTED)),
            hired=Count('id', filter=Q(status=Application.ApplicationStatus.HIRED)),
        )
        
        # Calculate conversion rate
        total = application_metrics['total_applications']
        hired = application_metrics['hired']
        conversion_rate = (hired / total * 100) if total > 0 else 0.0
        
        data = {
            'job_id': job.id,
            **application_metrics,
            'conversion_rate': conversion_rate,
        }
        
        serializer = JobAnalyticsSerializer(data)
        return Response(serializer.data)


class TopCandidatesView(APIView):
    """
    Top matched candidates for a job.
    
    GET /api/analytics/recruiter/jobs/<job_id>/top-candidates/
    
    Authentication required. Recruiter owner only.
    Returns top 20 candidates ordered by match_score DESC.
    """
    permission_classes = (IsAuthenticated, IsRecruiter, IsJobOwner)
    throttle_scope = 'analytics'

    def get_object(self, request, job_id):
        """Get job if owned by current recruiter"""
        try:
            return Job.objects.get(id=job_id, recruiter=request.user)
        except Job.DoesNotExist:
            raise Http404("Job not found")

    def get(self, request, job_id):
        """Get top candidates with query optimization"""
        job = self.get_object(request, job_id)
        
        # Get top candidates with select_related for candidate user
        # Ordered by match_score DESC, then by calculated_at DESC for tie-breaking, limited to TOP_CANDIDATES_LIMIT
        top_candidates = JobMatch.objects.filter(
            job=job
        ).select_related(
            'candidate'
        ).order_by(
            '-match_score',
            '-calculated_at'
        )[:TOP_CANDIDATES_LIMIT]
        
        # Serialize each candidate
        candidates_data = []
        for match in top_candidates:
            candidates_data.append({
                'candidate_id': match.candidate.id,
                'candidate_name': match.candidate.full_name or match.candidate.email,
                'match_score': float(match.match_score),
                'matched_skills_count': match.matched_skills_count,
                'total_required_skills': match.total_required_skills,
            })
        
        serializer = TopCandidateSerializer(candidates_data, many=True)
        return Response(serializer.data)
