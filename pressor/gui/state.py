from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GuiSessionState:
    """Mutable UI-facing state for the Pressor desktop app.

    This intentionally stays lightweight during the refactor. The goal in
    Phase 16 is to give the GUI a single, explicit home for transient state
    without changing behavior.
    """

    base_scan_results: list[dict[str, Any]] = field(default_factory=list)
    scan_results: list[dict[str, Any]] = field(default_factory=list)
    override_map: dict[str, str] = field(default_factory=dict)
    dropped_paths: list[Path] = field(default_factory=list)

    def clear_scan_results(self) -> None:
        self.base_scan_results.clear()
        self.scan_results.clear()

    def clear_overrides(self) -> None:
        self.override_map.clear()

    def clear_dropped_paths(self) -> None:
        self.dropped_paths.clear()
