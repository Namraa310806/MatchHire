"""Tests for the experience-match component (SPEC Decision 1 rules)."""

import math

import pytest

from api.matching.experience import experience_match


class TestNoRequirement:
    """Job specifies no experience requirement -> score 1.0 for all."""

    def test_both_fields_none_fresher(self):
        assert experience_match(0.0, None, None) == 1.0

    def test_both_fields_none_experienced(self):
        assert experience_match(5.0, None, None) == 1.0

    def test_both_fields_none_unknown(self):
        # SPEC: unknown candidate experience meets "no requirement" -> 1.0
        assert experience_match(None, None, None) == 1.0


class TestRequiredZero:
    """Job requires 0 years (fresher) -> 1.0 for any candidate."""

    def test_zero_required_zero_candidate(self):
        assert experience_match(0.0, 0.0) == 1.0

    def test_zero_required_experienced(self):
        assert experience_match(5.0, 0.0) == 1.0

    def test_zero_required_unknown(self):
        assert experience_match(None, 0.0) == 1.0

    def test_zero_min_with_max_is_range_including_zero(self):
        # "0-2 years" range includes 0 -> treat minimum as 0 -> 1.0
        assert experience_match(1.0, 0.0, 2.0) == 1.0
        assert experience_match(5.0, 0.0, 2.0) == 1.0
        assert experience_match(None, 0.0, 2.0) == 1.0


class TestPositiveMinimum:
    """Job requires positive minimum -> min(user/required, 1.0)."""

    def test_exact_minimum(self):
        assert experience_match(2.0, 2.0) == 1.0

    def test_above_minimum_capped(self):
        assert experience_match(5.0, 2.0) == 1.0

    def test_below_minimum_partial(self):
        assert experience_match(1.0, 2.0) == 0.5

    def test_zero_candidate_below_minimum(self):
        assert experience_match(0.0, 2.0) == 0.0

    def test_unknown_candidate_zero(self):
        # SPEC: user_yoe = null -> 0.0 when required_yoe > 0
        assert experience_match(None, 2.0) == 0.0

    def test_fractional_years(self):
        assert experience_match(1.5, 2.0) == 0.75


class TestRanges:
    """Job specifies a range like '2-5 years'."""

    def test_range_excluding_zero_uses_minimum(self):
        # "2-5 years", candidate 1 yr -> 1/2 = 0.5
        assert experience_match(1.0, 2.0, 5.0) == 0.5

    def test_range_candidate_at_minimum(self):
        assert experience_match(2.0, 2.0, 5.0) == 1.0

    def test_range_candidate_within(self):
        assert experience_match(3.0, 2.0, 5.0) == 1.0

    def test_range_candidate_above_not_penalized(self):
        # Overqualification is never penalized
        assert experience_match(10.0, 2.0, 5.0) == 1.0

    def test_range_excluding_zero_unknown_candidate(self):
        assert experience_match(None, 2.0, 5.0) == 0.0

    def test_max_only_range_includes_zero(self):
        # "up to 2 years" -> range includes 0 -> 1.0 for all
        assert experience_match(1.0, None, 2.0) == 1.0
        assert experience_match(None, None, 2.0) == 1.0


class TestValidation:
    def test_negative_user_yoe_rejected(self):
        with pytest.raises(ValueError, match="non-negative"):
            experience_match(-1.0, 2.0)

    def test_negative_required_rejected(self):
        with pytest.raises(ValueError, match="non-negative"):
            experience_match(1.0, -2.0)

    def test_nan_rejected(self):
        with pytest.raises(ValueError, match="finite"):
            experience_match(math.nan, 2.0)

    def test_inf_rejected(self):
        with pytest.raises(ValueError, match="finite"):
            experience_match(1.0, math.inf)

    def test_non_numeric_rejected(self):
        with pytest.raises(TypeError):
            experience_match("2", 2.0)  # type: ignore[arg-type]

    def test_score_bounds(self):
        for user in (None, 0.0, 0.5, 2.0, 100.0):
            for req in (None, 0.0, 1.0, 2.0, 10.0):
                score = experience_match(user, req)
                assert 0.0 <= score <= 1.0
