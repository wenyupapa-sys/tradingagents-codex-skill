#!/usr/bin/env python3
"""Validate a local TradingAgents Codex installation."""

from __future__ import annotations

import argparse
import json
import locale
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_PROJECT = str(Path.home() / "TradingAgents_codex")
REQUIRED_CODEX_ANALYZE_FLAGS = [
    "--model",
    "--ticker",
    "--analysis-date",
    "--analysts",
    "--search",
]
REQUIRED_CODEX_ANALYZE_FLAG_ALIASES = {
    "--reasoning-effort": ["--reasoning-effort", "--reasoning-effo"],
}


def resolve_project(raw: str | None) -> tuple[Path, str]:
    if raw:
        return Path(raw).expanduser().resolve(), "argument"
    env_path = os.environ.get("TRADINGAGENTS_PROJECT")
    if env_path:
        return Path(env_path).expanduser().resolve(), "TRADINGAGENTS_PROJECT"
    return Path(DEFAULT_PROJECT).resolve(), "default"


def run_cmd(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("NODE_OPTIONS", None)
    env.setdefault("COLUMNS", "240")
    env.setdefault("NO_COLOR", "1")
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=60)


def add_check(checks: list[dict[str, Any]], name: str, ok: bool, detail: str = "") -> None:
    checks.append({"name": name, "ok": ok, "detail": detail})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", help="Path to TradingAgents_codex project")
    parser.add_argument("--model", default="gpt-5.5", help="Default analysis model to look for in help output")
    args = parser.parse_args()

    project, source = resolve_project(args.project)
    checks: list[dict[str, Any]] = []

    add_check(checks, "project_exists", project.exists() and project.is_dir(), str(project))
    binary = project / ".venv" / "bin" / "tradingagents"
    add_check(checks, "tradingagents_binary", binary.exists() and os.access(binary, os.X_OK), str(binary))

    encoding = locale.getpreferredencoding(False) or ""
    add_check(checks, "utf8_locale", "UTF-8" in encoding.upper() or "UTF8" in encoding.upper(), encoding)

    env_test = subprocess.run(["env", "-u", "NODE_OPTIONS", "echo", "test"], capture_output=True, text=True)
    add_check(
        checks,
        "env_unset_node_options",
        env_test.returncode == 0 and env_test.stdout.strip() == "test",
        env_test.stderr.strip() or env_test.stdout.strip(),
    )

    if project.exists() and binary.exists():
        try:
            root_help = run_cmd([str(binary), "--help"], cwd=project)
            add_check(checks, "tradingagents_help", root_help.returncode == 0, root_help.stderr.strip())
        except Exception as exc:  # pragma: no cover - defensive CLI wrapper
            root_help = None
            add_check(checks, "tradingagents_help", False, repr(exc))

        try:
            analyze_help = run_cmd([str(binary), "codex-analyze", "--help"], cwd=project)
            help_text = (analyze_help.stdout or "") + "\n" + (analyze_help.stderr or "")
            add_check(checks, "codex_analyze_help", analyze_help.returncode == 0, analyze_help.stderr.strip())
            missing = [flag for flag in REQUIRED_CODEX_ANALYZE_FLAGS if flag not in help_text]
            for flag, aliases in REQUIRED_CODEX_ANALYZE_FLAG_ALIASES.items():
                if not any(alias in help_text for alias in aliases):
                    missing.append(flag)
            add_check(checks, "codex_analyze_required_flags", not missing, ", ".join(missing))
            add_check(checks, "default_model_visible", args.model in help_text, args.model)
        except Exception as exc:  # pragma: no cover - defensive CLI wrapper
            add_check(checks, "codex_analyze_help", False, repr(exc))
    else:
        add_check(checks, "tradingagents_help", False, "project or binary missing")
        add_check(checks, "codex_analyze_help", False, "project or binary missing")

    ok = all(check["ok"] for check in checks if check["name"] != "default_model_visible")
    result = {"ok": ok, "project": str(project), "project_source": source, "checks": checks}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
