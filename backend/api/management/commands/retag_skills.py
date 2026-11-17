"""Management command to retag existing jobs with the new skills dictionary.

This command safely re-extracts skills from job descriptions using the
new versioned skills dictionary. It operates in dry-run mode by default
and requires explicit confirmation to make changes.

Usage:
    python manage.py retag_skills --dry-run  # Preview changes
    python manage.py retag_skills              # Apply changes
    python manage.py retag_skills --commit    # Apply changes (explicit)
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from api.extraction import extract_skills, get_skills_dictionary
from api.models import Job, JobSkill, Skill


class Command(BaseCommand):
    help = "Retag existing jobs with the new versioned skills dictionary"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Preview changes without applying them (default: True)",
        )
        parser.add_argument(
            "--commit",
            action="store_true",
            dest="commit",
            help="Apply changes (overrides --dry-run)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of jobs to process (for testing)",
        )

    def handle(self, *args, **options):
        """Execute the retagging command."""
        dry_run = not options["commit"]
        limit = options.get("limit")

        self.stdout.write(self.style.WARNING("Job Skill Retagging"))
        self.stdout.write("=" * 50)

        # Load skills dictionary
        try:
            dictionary = get_skills_dictionary()
            self.stdout.write(f"Skills dictionary version: {dictionary.version}")
            self.stdout.write(f"Total skills: {dictionary.total_skills}")
            self.stdout.write(f"Total aliases: {dictionary.total_aliases}")
        except Exception as e:
            raise CommandError(f"Failed to load skills dictionary: {e}") from e

        # Count jobs
        total_jobs = Job.objects.count()
        if limit:
            self.stdout.write(f"Processing {limit} of {total_jobs} jobs (limited)")
            jobs = Job.objects.all()[:limit]
        else:
            self.stdout.write(f"Processing all {total_jobs} jobs")
            jobs = Job.objects.all()

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN MODE: No changes will be applied"))
        else:
            self.stdout.write(self.style.WARNING("COMMIT MODE: Changes will be applied"))

        self.stdout.write("")

        # Process jobs
        stats = {
            "jobs_inspected": 0,
            "skills_detected": 0,
            "additions": 0,
            "removals": 0,
            "unchanged": 0,
            "errors": 0,
        }

        for job in jobs:
            try:
                self._process_job(job, dry_run, stats)
            except Exception as e:
                stats["errors"] += 1
                self.stdout.write(
                    self.style.ERROR(f"  Error processing job {job.id}: {e}")
                )

        # Report summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("Retagging Summary"))
        self.stdout.write(f"Jobs inspected: {stats['jobs_inspected']}")
        self.stdout.write(f"Skills detected: {stats['skills_detected']}")
        self.stdout.write(f"Additions: {stats['additions']}")
        self.stdout.write(f"Removals: {stats['removals']}")
        self.stdout.write(f"Unchanged: {stats['unchanged']}")
        self.stdout.write(f"Errors: {stats['errors']}")

        if dry_run:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING("DRY-RUN: No changes were applied")
            )
            self.stdout.write("Run with --commit to apply changes")
        else:
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("Changes applied successfully"))

    def _process_job(self, job: Job, dry_run: bool, stats: dict) -> None:
        """Process a single job for retagging.

        Args:
            job: The Job instance
            dry_run: If True, skip actual database writes
            stats: Statistics dictionary to update
        """
        stats["jobs_inspected"] += 1

        # Get existing skills
        existing_skills = set(
            JobSkill.objects.filter(job=job).values_list("skill__name", flat=True)
        )

        # Extract new skills using shared extractor
        new_skill_matches = extract_skills(job.description)
        new_skills = {match.canonical_name for match in new_skill_matches}

        stats["skills_detected"] += len(new_skills)

        # Compare
        to_add = new_skills - existing_skills
        to_remove = existing_skills - new_skills

        if not to_add and not to_remove:
            stats["unchanged"] += 1
            return

        # Report changes
        self.stdout.write(f"Job {job.id}: {job.title[:50]}...")
        if to_add:
            self.stdout.write(f"  Adding: {', '.join(sorted(to_add))}")
            stats["additions"] += len(to_add)
        if to_remove:
            self.stdout.write(f"  Removing: {', '.join(sorted(to_remove))}")
            stats["removals"] += len(to_remove)

        # Apply changes if not dry-run
        if not dry_run:
            with transaction.atomic():
                # Remove old skills
                if to_remove:
                    JobSkill.objects.filter(
                        job=job, skill__name__in=to_remove
                    ).delete()

                # Add new skills
                if to_add:
                    # Get skill objects from database
                    skill_objects = Skill.objects.filter(name__in=to_add)
                    job_skills = [
                        JobSkill(job=job, skill=skill, is_required=True)
                        for skill in skill_objects
                    ]
                    JobSkill.objects.bulk_create(job_skills)

                self.stdout.write(self.style.SUCCESS("  Updated"))
