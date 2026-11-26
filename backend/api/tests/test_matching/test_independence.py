"""Prove the matching core imports without Django initialization.

Runs ``api.matching`` in a subprocess with no DJANGO_SETTINGS_MODULE
and asserts the import succeeds and match() works. If any module in
the chain imported django, settings would be unconfigured and the
import would fail.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]


def test_matching_core_imports_without_django():
    code = textwrap.dedent(
        """
        import sys
        assert "django" not in sys.modules or True  # django may be installed
        # The real check: no DJANGO_SETTINGS_MODULE is configured, so any
        # django settings access would raise. Importing api.matching must
        # not touch django at all.
        from api.matching import (
            UNIFORM_VECTORIZER,
            CandidateInput,
            JobInput,
            match,
        )
        result = match(
            CandidateInput.from_iterables(skills=["Python"], total_experience_years=1.0),
            JobInput.from_iterables(skills=["Python"], experience_min_years=1.0),
            vectorizer=UNIFORM_VECTORIZER,
        )
        # skills 1.0*0.5 + experience 1.0*0.3 + keywords 0.0*0.2 = 0.8
        assert abs(result.total_score - 0.8) < 1e-9, result
        # Prove django was never imported by the matching chain.
        django_modules = [m for m in sys.modules if m == "django" or m.startswith("django.")]
        assert not django_modules, f"django modules loaded: {django_modules}"
        print("OK")
        """
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, f"stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    assert "OK" in proc.stdout
