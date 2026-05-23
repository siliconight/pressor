"""Backward-compatible import shim for older Pressor code and tests.

The implementation now lives in pressor.legacy_encoder so the repo root can stay focused on user-facing entry points.
"""
from pressor.legacy_encoder import *  # noqa: F401,F403
