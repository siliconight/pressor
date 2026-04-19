
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from encoder import EncoderError


def default_workspace_root() -> Path:
    if os.name == "nt":
        return Path("C:/Pressor")
    return Path.home() / "Pressor"


def settings_dir() -> Path:
    return Path.home() / ".pressor"


def global_workspace_config_path() -> Path:
    return settings_dir() / "workspace.json"


def local_workspace_config_path(workspace_root: Path) -> Path:
    return workspace_root / "pressor.workspace.json"


def workspace_config_payload(workspace_root: Path) -> Dict[str, str]:
    root = workspace_root.resolve()
    return {
        "workspace_root": str(root),
        "input_path": str(root / "input"),
        "output_path": str(root / "output"),
    }


def save_workspace_config(payload: Dict[str, Any]) -> Path:
    root = Path(str(payload["workspace_root"])).resolve()
    settings_dir().mkdir(parents=True, exist_ok=True)
    global_path = global_workspace_config_path()
    global_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    local_path = local_workspace_config_path(root)
    local_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return global_path


def load_workspace_config() -> Dict[str, str] | None:
    candidates = [global_workspace_config_path(), local_workspace_config_path(default_workspace_root())]
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        if {"workspace_root", "input_path", "output_path"} <= set(data.keys()):
            return {
                "workspace_root": str(data["workspace_root"]),
                "input_path": str(data["input_path"]),
                "output_path": str(data["output_path"]),
            }
    return None


def initialize_workspace(root_path: str | Path | None = None) -> Dict[str, str]:
    workspace_root = Path(root_path) if root_path else default_workspace_root()
    workspace_root = workspace_root.expanduser().resolve()
    (workspace_root / "input").mkdir(parents=True, exist_ok=True)
    (workspace_root / "output").mkdir(parents=True, exist_ok=True)
    payload = workspace_config_payload(workspace_root)
    save_workspace_config(payload)
    return payload


def ensure_workspace_initialized(root_path: str | Path | None = None) -> Dict[str, str]:
    existing = load_workspace_config()
    if existing:
        return existing
    return initialize_workspace(root_path)


def resolve_default_input_output() -> tuple[Path, Path]:
    cfg = ensure_workspace_initialized()
    return Path(cfg["input_path"]), Path(cfg["output_path"])


def describe_workspace(cfg: Dict[str, str]) -> str:
    return f"Workspace root: {cfg['workspace_root']}\nInput: {cfg['input_path']}\nOutput: {cfg['output_path']}"
