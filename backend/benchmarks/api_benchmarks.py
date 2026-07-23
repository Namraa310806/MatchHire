"""
API Performance Benchmarks for MatchHire Backend

This script provides benchmarking utilities to measure API endpoint performance
before and after optimizations. Uses Django test framework for consistent measurements.

Usage:
    python manage.py benchmark_api
    python manage.py benchmark_api --endpoint jobs/list
    python manage.py benchmark_api --all
"""

import time
import statistics
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate

from apps.jobs.models import Job
from apps.resumes.models import Resume
from apps.matching.models import JobMatch

User = get_user_model()


class BenchmarkResult:
    """Container for benchmark results"""

    def __init__(self, name):
        self.name = name
        self.durations = []
        self.query_counts = []

    def add_measurement(self, duration, query_count):
        self.durations.append(duration)
        self.query_counts.append(query_count)

    def get_stats(self):
        if not self.durations:
            return None

        return {
            "name": self.name,
            "count": len(self.durations),
            "duration_mean_ms": statistics.mean(self.durations) * 1000,
            "duration_median_ms": statistics.median(self.durations) * 1000,
            "duration_min_ms": min(self.durations) * 1000,
            "duration_max_ms": max(self.durations) * 1000,
            "duration_p95_ms": (
                statistics.quantiles(self.durations, n=20)[18] * 1000
                if len(self.durations) >= 20
                else max(self.durations) * 1000
            ),
            "query_count_mean": statistics.mean(self.query_counts),
            "query_count_max": max(self.query_counts),
        }


class APIBenchmarker:
    """Benchmark utility for API endpoints"""

    def __init__(self, iterations=10):
        self.iterations = iterations
        self.factory = APIRequestFactory()
        self.results = {}

    def benchmark_endpoint(self, name, view_func, request, user=None):
        """
        Benchmark a single endpoint.

        Args:
            name: Benchmark name
            view_func: View function to benchmark
            request: Request object
            user: User for authentication (optional)
        """
        from django.db import connection

        result = BenchmarkResult(name)

        for _ in range(self.iterations):
            # Reset connection to ensure clean state
            connection.close()

            # Authenticate if user provided
            if user:
                force_authenticate(request, user=user)

            # Measure query count
            connection.queries_log.clear()

            # Measure duration
            start_time = time.perf_counter()

            try:
                view_func(request)
            except Exception as e:
                print(f"Error benchmarking {name}: {e}")
                continue

            end_time = time.perf_counter()
            duration = end_time - start_time
            query_count = len(connection.queries)

            result.add_measurement(duration, query_count)

        self.results[name] = result
        return result

    def print_results(self):
        """Print benchmark results"""
        print("\n" + "=" * 80)
        print("API PERFORMANCE BENCHMARK RESULTS")
        print("=" * 80)

        for name, result in self.results.items():
            stats = result.get_stats()
            if stats:
                print(f'\n{stats["name"]}:')
                print(f"  Iterations: {stats['count']}")
                print("  Duration (ms):")
                print(f"    Mean:   {stats['duration_mean_ms']:.2f}")
                print(f"    Median: {stats['duration_median_ms']:.2f}")
                print(f"    Min:    {stats['duration_min_ms']:.2f}")
                print(f"    Max:    {stats['duration_max_ms']:.2f}")
                print(f"    P95:    {stats['duration_p95_ms']:.2f}")
                print("  Query Count:")
                print(f"    Mean:   {stats['query_count_mean']:.1f}")
                print(f"    Max:    {stats['query_count_max']}")

        print("\n" + "=" * 80)


class Command(BaseCommand):
    help = "Run API performance benchmarks"

    def add_arguments(self, parser):
        parser.add_argument(
            "--endpoint",
            type=str,
            help="Specific endpoint to benchmark (e.g., jobs/list, dashboard/candidate)",
        )
        parser.add_argument(
            "--iterations",
            type=int,
            default=10,
            help="Number of iterations per benchmark (default: 10)",
        )
        parser.add_argument("--all", action="store_true", help="Run all benchmarks")

    def handle(self, *args, **options):
        iterations = options["iterations"]
        endpoint = options.get("endpoint")
        run_all = options.get("all", False)

        self.stdout.write(f"Running API benchmarks with {iterations} iterations...")

        benchmarker = APIBenchmarker(iterations=iterations)

        # Setup test data
        self._setup_test_data()

        if run_all or not endpoint:
            self._run_all_benchmarks(benchmarker)
        elif endpoint == "jobs/list":
            self._benchmark_jobs_list(benchmarker)
        elif endpoint == "jobs/recommendations":
            self._benchmark_job_recommendations(benchmarker)
        elif endpoint == "dashboard/candidate":
            self._benchmark_candidate_dashboard(benchmarker)
        elif endpoint == "dashboard/recruiter":
            self._benchmark_recruiter_dashboard(benchmarker)
        elif endpoint == "resumes/list":
            self._benchmark_resumes_list(benchmarker)
        else:
            self.stdout.write(f"Unknown endpoint: {endpoint}")
            return

        benchmarker.print_results()

    def _setup_test_data(self):
        """Setup minimal test data for benchmarks"""
        self.stdout.write("Setting up test data...")

        # Create test users
        self.candidate = User.objects.create_user(
            email="candidate@example.com",
            password="testpass123",
            role=User.Roles.CANDIDATE,
            full_name="Test Candidate",
        )

        self.recruiter = User.objects.create_user(
            email="recruiter@example.com",
            password="testpass123",
            role=User.Roles.RECRUITER,
            full_name="Test Recruiter",
        )

        # Create test jobs
        for i in range(10):
            Job.objects.create(
                recruiter=self.recruiter,
                title=f"Test Job {i}",
                company_name="Test Company",
                location="Remote",
                description="Test description",
                status=Job.JobStatus.ACTIVE,
            )

    def _run_all_benchmarks(self, benchmarker):
        """Run all benchmarks"""
        self._benchmark_jobs_list(benchmarker)
        self._benchmark_job_recommendations(benchmarker)
        self._benchmark_candidate_dashboard(benchmarker)
        self._benchmark_recruiter_dashboard(benchmarker)
        self._benchmark_resumes_list(benchmarker)

    def _benchmark_jobs_list(self, benchmarker):
        """Benchmark public jobs list endpoint"""
        from apps.jobs.views import PublicJobListView

        view = PublicJobListView.as_view()
        request = benchmarker.factory.get("/api/jobs/public/")

        benchmarker.benchmark_endpoint("GET /api/jobs/public/", view, request)

    def _benchmark_job_recommendations(self, benchmarker):
        """Benchmark job recommendations endpoint"""
        from apps.matching.views import JobRecommendationsView

        # Create some job matches for the candidate
        jobs = Job.objects.filter(status=Job.JobStatus.ACTIVE)[:5]
        for job in jobs:
            JobMatch.objects.create(
                candidate=self.candidate,
                job=job,
                match_score=85.5,
                skills_score=90.0,
                experience_score=80.0,
                education_score=100.0,
                matched_skills_count=5,
                total_required_skills=6,
            )

        view = JobRecommendationsView.as_view()
        request = benchmarker.factory.get("/api/jobs/recommendations/")

        benchmarker.benchmark_endpoint(
            "GET /api/jobs/recommendations/", view, request, user=self.candidate
        )

    def _benchmark_candidate_dashboard(self, benchmarker):
        """Benchmark candidate dashboard endpoint"""
        from apps.analytics.views import CandidateDashboardView

        view = CandidateDashboardView.as_view()
        request = benchmarker.factory.get("/api/analytics/candidate/dashboard/")

        benchmarker.benchmark_endpoint(
            "GET /api/analytics/candidate/dashboard/",
            view,
            request,
            user=self.candidate,
        )

    def _benchmark_recruiter_dashboard(self, benchmarker):
        """Benchmark recruiter dashboard endpoint"""
        from apps.analytics.views import RecruiterDashboardView

        view = RecruiterDashboardView.as_view()
        request = benchmarker.factory.get("/api/analytics/recruiter/dashboard/")

        benchmarker.benchmark_endpoint(
            "GET /api/analytics/recruiter/dashboard/",
            view,
            request,
            user=self.recruiter,
        )

    def _benchmark_resumes_list(self, benchmarker):
        """Benchmark resumes list endpoint"""
        from apps.resumes.views import ResumeListView

        # Create test resume
        Resume.objects.create(user=self.candidate)

        view = ResumeListView.as_view()
        request = benchmarker.factory.get("/api/resumes/")

        benchmarker.benchmark_endpoint(
            "GET /api/resumes/", view, request, user=self.candidate
        )
