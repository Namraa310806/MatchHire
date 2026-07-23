from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("matching", "0003_remove_jobmatch_jobmatch_job_match_score_idx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="JobSkill",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                (
                    "job",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="required_skills",
                        to="jobs.job",
                    ),
                ),
            ],
            options={
                "db_table": "job_skills",
                "verbose_name": "job skill",
                "verbose_name_plural": "job skills",
                "ordering": ["name"],
            },
        ),
        migrations.AddConstraint(
            model_name="jobskill",
            constraint=models.UniqueConstraint(
                fields=("job", "name"),
                name="unique_job_skill_name",
                violation_error_message="A job cannot list the same required skill twice.",
            ),
        ),
        migrations.AddIndex(
            model_name="jobskill",
            index=models.Index(fields=["job"], name="job_skills_job_idx"),
        ),
    ]