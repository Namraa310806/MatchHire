# Generated migration for performance optimization
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0001_initial"),
    ]

    operations = [
        # PERFORMANCE OPTIMIZATION: Composite index for status + created_at
        # Improves query performance for public job list (filter by status, order by created_at)
        migrations.AddIndex(
            model_name="job",
            index=models.Index(
                fields=["status", "-created_at"],
                name="jobs_status_created_at_idx",
            ),
        ),
    ]
