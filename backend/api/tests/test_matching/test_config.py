"""Tests for MatchConfig weight validation."""

import math
from dataclasses import FrozenInstanceError

import pytest

from api.matching.config import DEFAULT_CONFIG, MatchConfig


class TestMatchConfig:
    def test_defaults_match_spec(self):
        assert DEFAULT_CONFIG.skill_weight == 0.50
        assert DEFAULT_CONFIG.experience_weight == 0.30
        assert DEFAULT_CONFIG.keyword_weight == 0.20

    def test_custom_valid_weights(self):
        config = MatchConfig(skill_weight=0.6, experience_weight=0.2, keyword_weight=0.2)
        assert config.skill_weight == 0.6

    def test_weights_must_sum_to_one(self):
        with pytest.raises(ValueError, match="sum to 1.0"):
            MatchConfig(skill_weight=0.5, experience_weight=0.3, keyword_weight=0.1)

    def test_negative_weight_rejected(self):
        with pytest.raises(ValueError, match="non-negative"):
            MatchConfig(skill_weight=-0.1, experience_weight=0.6, keyword_weight=0.5)

    def test_nan_weight_rejected(self):
        with pytest.raises(ValueError, match="finite"):
            MatchConfig(skill_weight=math.nan, experience_weight=0.5, keyword_weight=0.5)

    def test_infinite_weight_rejected(self):
        with pytest.raises(ValueError, match="finite"):
            MatchConfig(
                skill_weight=math.inf, experience_weight=0.5, keyword_weight=0.5
            )

    def test_zero_weights_allowed_if_sum_is_one(self):
        config = MatchConfig(skill_weight=1.0, experience_weight=0.0, keyword_weight=0.0)
        assert config.skill_weight == 1.0

    def test_non_numeric_weight_rejected(self):
        with pytest.raises(TypeError):
            MatchConfig(
                skill_weight="0.5",  # type: ignore[arg-type]
                experience_weight=0.3,
                keyword_weight=0.2,
            )

    def test_frozen(self):
        with pytest.raises(FrozenInstanceError):
            DEFAULT_CONFIG.skill_weight = 0.9  # type: ignore[misc]
