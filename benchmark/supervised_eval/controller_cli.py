"""Command-line boundary for advancing a real pilot under active supervision."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contracts import InterventionClass, TerminalClass
from .controller import PilotRunController


def _json(value: str) -> dict:
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("must be a JSON object")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Advance one durable supervised-evaluation action")
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("--manifest", required=True, type=_json)
    create.add_argument("--endpoint", required=True)
    create.add_argument("--model", required=True)
    create.add_argument("--workspace", required=True, type=Path)
    create.add_argument("--message-file", required=True, type=Path)
    create.add_argument("--request-options", type=_json, default={})
    create.add_argument("--tool-environment", type=_json, default={})
    checkpoint = commands.add_parser("checkpoint")
    checkpoint.add_argument("--decision", required=True)
    checkpoint.add_argument("--basis", required=True)
    checkpoint.add_argument("--progress", action="store_true")
    commands.add_parser("turn")
    intervene = commands.add_parser("intervene")
    intervene.add_argument("--class", dest="intervention_class", required=True, choices=[item.value for item in InterventionClass])
    intervene.add_argument("--text-file", required=True, type=Path)
    intervene.add_argument("--basis", required=True)
    terminal = commands.add_parser("terminal")
    terminal.add_argument("--class", dest="terminal_class", required=True, choices=[item.value for item in TerminalClass])
    terminal.add_argument("--reason", required=True)
    terminal.add_argument("--summary-file", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "create":
        controller = PilotRunController.create(
            args.evidence_root, args.run_id, manifest=args.manifest, endpoint=args.endpoint,
            model=args.model, workspace=args.workspace,
            initial_message=args.message_file.read_text(encoding="utf-8"),
            request_options=args.request_options, tool_environment=args.tool_environment,
        )
        print(json.dumps({"created": controller.state_path.as_posix()}))
        return 0
    controller = PilotRunController(args.evidence_root, args.run_id)
    if args.command == "checkpoint":
        controller.checkpoint(decision=args.decision, basis=args.basis, progress_observed=args.progress)
        print(json.dumps({"checkpoint": controller.state["supervision_checkpoints"]}))
    elif args.command == "turn":
        print(json.dumps(controller.one_turn().compact(), sort_keys=True))
    elif args.command == "intervene":
        controller.intervene(InterventionClass(args.intervention_class), args.text_file.read_text(encoding="utf-8"), args.basis)
        print(json.dumps({"intervention": args.intervention_class}))
    else:
        controller.terminal(TerminalClass(args.terminal_class), args.reason, args.summary_file.read_text(encoding="utf-8"))
        print(json.dumps({"terminal": args.terminal_class}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
