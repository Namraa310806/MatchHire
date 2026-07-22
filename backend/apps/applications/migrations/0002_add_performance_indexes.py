# Generated migration for performance optimization
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0001_initial"),
    ]

    operations = [
        # PERFORMANCE OPTIMIZATION: Composite index for job + status
        # Improves query performance for job applications list (filter by job and status)
        migrations.AddIndex(
            model_name="application",
            index=models.Index(
                fields=["job", "status"],
                name="applications_job_status_idx",
            ),
        ),
    ]
