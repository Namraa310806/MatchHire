"""Tests for eval dataset loading and validation."""

import csv
from pathlib import Path

import pytest

from eval.dataset import (
    NEEDS_REVIEW,
    load_dataset,
    load_labels,
    relevance_for,
)

DATASET_DIR = Path(__file__).resolve().parents[3] / "eval"


@pytest.fixture(scope="module")
def dataset():
    return load_dataset(DATASET_DIR)


class TestDatasetShape:
    def test_ten_candidates(self, dataset):
        assert len(dataset.candidates) == 10

    def test_sixty_jobs(self, dataset):
        assert len(dataset.jobs) == 60

    def test_all_pairs_labeled(self, dataset):
        assert len(dataset.labels) == 10 * 60

    def test_candidate_archetypes_present(self, dataset):
        ids = {c.candidate_id for c in dataset.candidates}
        assert {
            "c01_ml_fresher",
            "c02_frontend_react_fresher",
            "c03_devops_engineer",
            "c04_vlsi_embedded",
            "c07_android_dev",
            "c10_fullstack_unknown",
        } <= ids

    def test_experience_variety(self, dataset):
        yoes = [c.total_experience_years for c in dataset.candidates]
        assert None in yoes  # unknown experience case
        assert 0.0 in yoes  # explicit zero experience case
        assert any(y is not None and y > 0 for y in yoes)

    def test_job_experience_variety(self, dataset):
        mins = [j.experience_min_years for j in dataset.jobs]
        assert None in mins  # no stated requirement
        assert 0.0 in mins  # fresher-friendly
        assert any(m is not None and m > 0 for m in mins)

    def test_skills_and_keywords_are_separate_fields(self, dataset):
        for c in dataset.candidates:
            # skills and domain keywords are distinct sets, not merged
            assert isinstance(c.skills, tuple)
            assert isinstance(c.domain_keywords, tuple)


class TestLabelValidity:
    def test_relevance_values_valid(self, dataset):
        for label in dataset.labels:
            assert label.relevance is None or label.relevance in (0, 1, 2)

    def test_label_distribution_has_all_levels(self, dataset):
        values = {label.relevance for label in dataset.labels if label.relevance is not None}
        assert values == {0, 1, 2}

    def test_some_needs_review_or_none(self, dataset):
        # needs-review is allowed but must be a deliberate minority
        nr = sum(1 for label in dataset.labels if label.relevance is None)
        assert nr < len(dataset.labels) // 10

    def test_relevance_for_lookup(self, dataset):
        rel = relevance_for(dataset, "c01_ml_fresher", "j02")
        assert rel in (0, 1, 2, None)


class TestValidationRejectsBadData:
    def _write(self, directory: Path, name: str, fieldnames: list[str], rows: list[dict]):
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / name).open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def test_missing_pair_rejected(self, tmp_path):
        d = tmp_path / "ds"
        self._write(
            d, "candidates.csv",
            ["candidate_id", "skills", "domain_keywords", "total_experience_years", "note"],
            [{"candidate_id": "c1", "skills": "Python", "domain_keywords": "", "total_experience_years": "", "note": ""}],
        )
        self._write(
            d, "jobs.csv",
            ["job_id", "title", "company", "skills", "domain_keywords", "experience_min_years", "experience_max_years", "location", "role_type"],
            [
                {"job_id": "j1", "title": "A", "company": "X", "skills": "Python", "domain_keywords": "", "experience_min_years": "", "experience_max_years": "", "location": "", "role_type": ""},
                {"job_id": "j2", "title": "B", "company": "Y", "skills": "Go", "domain_keywords": "", "experience_min_years": "", "experience_max_years": "", "location": "", "role_type": ""},
            ],
        )
        # Only one of two pairs labeled
        self._write(
            d, "labels.csv",
            ["candidate_id", "job_id", "relevance"],
            [{"candidate_id": "c1", "job_id": "j1", "relevance": "2"}],
        )
        with pytest.raises(ValueError, match="missing labels"):
            load_dataset(d)

    def test_invalid_relevance_rejected(self, tmp_path):
        d = tmp_path / "ds"
        self._write(
            d, "candidates.csv",
            ["candidate_id", "skills", "domain_keywords", "total_experience_years", "note"],
            [{"candidate_id": "c1", "skills": "Python", "domain_keywords": "", "total_experience_years": "", "note": ""}],
        )
        self._write(
            d, "jobs.csv",
            ["job_id", "title", "company", "skills", "domain_keywords", "experience_min_years", "experience_max_years", "location", "role_type"],
            [{"job_id": "j1", "title": "A", "company": "X", "skills": "Python", "domain_keywords": "", "experience_min_years": "", "experience_max_years": "", "location": "", "role_type": ""}],
        )
        self._write(
            d, "labels.csv",
            ["candidate_id", "job_id", "relevance"],
            [{"candidate_id": "c1", "job_id": "j1", "relevance": "5"}],
        )
        with pytest.raises(ValueError, match="Relevance"):
            load_labels(d / "labels.csv")

    def test_needs_review_parses_to_none(self, tmp_path):
        d = tmp_path / "lbl.csv"
        d.write_text(
            "candidate_id,job_id,relevance\nc1,j1,needs-review\n", encoding="utf-8"
        )
        labels = load_labels(d)
        assert labels[0].relevance is None
        assert NEEDS_REVIEW == "needs-review"
