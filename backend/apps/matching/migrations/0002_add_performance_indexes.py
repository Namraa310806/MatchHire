# Generated migration for performance optimization
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("matching", "0001_initial"),
    ]

    operations = [
        # PERFORMANCE OPTIMIZATION: Composite index for job + match_score
        # Improves query performance for top candidates view (filter by job, order by match_score DESC)
        migrations.AddIndex(
            model_name="jobmatch",
            index=models.Index(
                fields=["job", "-match_score"],
                name="jobmatch_job_match_score_idx",
            ),
        ),
        # PERFORMANCE OPTIMIZATION: Composite index for candidate + job
        # The unique constraint already serves as an index, but we add an explicit one for clarity
        # This improves query performance for candidate match lookups
        migrations.AddIndex(
            model_name="jobmatch",
            index=models.Index(
                fields=["candidate", "job"],
                name="jobmatch_candidate_job_idx",
            ),
        ),
    ]
