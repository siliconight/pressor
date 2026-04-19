from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable, Type

from pressor.cli.args import parse_args
from pressor.core.paths import find_supported_audio_files
from pressor.core.workspace import (
    default_workspace_root,
    describe_workspace,
    ensure_workspace_initialized,
    initialize_workspace,
    load_workspace_config,
)



Namespace = argparse.Namespace
RunFn = Callable[[Namespace], int]
GuiFn = Callable[[list[str] | None], int]


def _prompt_workspace_root() -> str | None:
    default_root = str(default_workspace_root())
    try:
        reply = input(f"Pressor workspace root [{default_root}]: ").strip()
    except EOFError:
        reply = ""
    return reply or default_root


def _apply_workspace_defaults(args: Namespace) -> int | None:
    if args.show_workspace:
        cfg = load_workspace_config()
        if not cfg:
            cfg = ensure_workspace_initialized()
        print(describe_workspace(cfg))
        return 0

    if args.init:
        root = args.workspace_root or _prompt_workspace_root()
        cfg = initialize_workspace(root)
        print("Pressor workspace initialized.")
        print(describe_workspace(cfg))
        return 0

    if args.selftest or args.doctor or args.gui or args.paths or args.manifest or args.build_manifest:
        return None

    if not args.input and not args.output:
        if load_workspace_config() is None:
            root = _prompt_workspace_root() if sys.stdin.isatty() else str(default_workspace_root())
            cfg = initialize_workspace(root)
            print("Pressor workspace initialized.")
            print(describe_workspace(cfg))
            print("")
            print("Pressor created a default workspace for you.")
            print("Drop source-quality audio files into the input folder, then run Pressor again.")
            print(f"Input folder : {cfg['input_path']}")
            print(f"Output root  : {cfg['output_path']}")
            input_path = Path(cfg["input_path"])
            if not find_supported_audio_files(input_path):
                print("")
                print("No supported audio files were found yet, so Pressor did not start a run.")
                return 0
        else:
            cfg = ensure_workspace_initialized()
            input_path = Path(cfg["input_path"])
            if not find_supported_audio_files(input_path):
                print("Pressor workspace found.")
                print(describe_workspace(cfg))
                print("")
                print("No supported audio files were found in the workspace input folder.")
                print("Add source-quality audio files to the input folder, then run Pressor again.")
                return 0
        args.input = cfg["input_path"]
        args.output = cfg["output_path"]
    elif (args.input and not args.output) or (args.output and not args.input):
        cfg = ensure_workspace_initialized()
        if not args.input:
            args.input = cfg["input_path"]
        if not args.output:
            args.output = cfg["output_path"]
    return None


def dispatch_args(
    args: Namespace,
    *,
    run_selftest: RunFn,
    run_doctor: RunFn,
    run_gui: GuiFn,
    run_cli: RunFn,
    error_type: Type[BaseException],
) -> int:
    try:
        workspace_result = _apply_workspace_defaults(args)
        if workspace_result is not None:
            return workspace_result
        if args.selftest:
            return run_selftest(args)
        if args.doctor:
            return run_doctor(args)
        if args.gui or args.paths:
            return run_gui(args.paths)
        if not args.input and not args.manifest:
            print(
                "Either use --gui, --selftest, --doctor, drag files onto Pressor, provide --input, or run with --manifest.",
                file=sys.stderr,
            )
            return 2
        return run_cli(args)
    except error_type as exc:
        print(str(exc), file=sys.stderr)
        return 2



def main(
    *,
    argv: list[str] | None = None,
    run_selftest: RunFn,
    run_doctor: RunFn,
    run_gui: GuiFn,
    run_cli: RunFn,
    error_type: Type[BaseException],
) -> int:
    args = parse_args(argv)
    return dispatch_args(
        args,
        run_selftest=run_selftest,
        run_doctor=run_doctor,
        run_gui=run_gui,
        run_cli=run_cli,
        error_type=error_type,
    )
