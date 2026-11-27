"""Golden evaluation harness for the v0 matching engine.

Pure Python + stdlib CSV. No Django models, no database, no Redis, no
Celery, no network. The matcher is used unmodified; this package only
loads the dataset, scores pairs, and computes ranking metrics.
"""
