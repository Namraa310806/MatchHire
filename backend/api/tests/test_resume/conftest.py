"""Shared fixtures for resume pipeline tests.

Celery's ``task_always_eager`` does not affect ``apply_async``/``send_task``
(Celery 5.x), so tests route task dispatch through synchronous ``apply()``
while keeping the production code path (``apply_async``) intact.
"""

import pytest


@pytest.fixture(autouse=True)
def _eager_resume_dispatch(monkeypatch):
    """Make resume task dispatch synchronous in tests."""
    from api.tasks import parse_resume_task

    def _apply_async(args=None, kwargs=None, task_id=None, **_kwargs):
        return parse_resume_task.apply(args=args, kwargs=kwargs, task_id=task_id)

    monkeypatch.setattr(
        "api.resume.views.parse_resume_task.apply_async", _apply_async
    )
