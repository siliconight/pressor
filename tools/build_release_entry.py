#!/usr/bin/env python3
"""Backward-compatible wrapper for the release builder."""
from tools.build_release import main

if __name__ == "__main__":
    raise SystemExit(main())
