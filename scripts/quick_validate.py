#!/usr/bin/env python3
"""Validate the tradingagents-codex skill without live analysis."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


REQUIRED_SECTIONS = ["## Triggers", "## Workflow", "## Safety"]
REQUIRED_SCRIPTS = ["check_setup.py", "run_analysis.py", "summarize_report.py"]


def add(checks: list[dict[str, Any]], name: str, ok: bool, detail: str = "") -> None:
    checks.append({"name": name, "ok": ok, "detail": detail})


def import_script(path: Path) -> bool:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        return False
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return True


def run_help(path: Path) -> tuple[bool, str]:
    proc = subprocess.run([sys.executable, str(path), "--help"], capture_output=True, text=True, timeout=20)
    return proc.returncode == 0, proc.stderr.strip() or proc.stdout.splitlines()[0]


def fixture_summary_test(skill_dir: Path) -> tuple[bool, str]:
    script = skill_dir / "scripts" / "summarize_report.py"
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp)
        report_dir = project / "codex_runs" / "FAKE" / "2026-01-02" / "reports"
        report_dir.mkdir(parents=True)
        (report_dir / "complete_report.md").write_text("# fake\n", encoding="utf-8")
        (report_dir / "portfolio_manager.json").write_text(
            json.dumps(
                {
                    "ticker": "FAKE",
                    "analysis_date": "2026-01-02",
                    "rating": "Hold",
                    "time_horizon": "1-2 weeks",
                    "summary": "Fixture summary.",
                    "positioning": {"entry": "Wait", "size": "Small", "stop": "N/A", "take_profit": "N/A"},
                    "top_reasons": ["Reason A"],
                    "top_risks": ["Risk A"],
                }
            ),
            encoding="utf-8",
        )
        proc = subprocess.run(
            [
                sys.executable,
                str(script),
                "--project",
                str(project),
                "--ticker",
                "FAKE",
                "--date",
                "2026-01-02",
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )
        return proc.returncode == 0 and "Fixture summary" in proc.stdout, proc.stderr.strip() or proc.stdout[:120]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-dir", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--project", help="Optional real TradingAgents_codex project for integration check")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).expanduser().resolve()
    checks: list[dict[str, Any]] = []

    skill_md = skill_dir / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8") if skill_md.exists() else ""
    add(checks, "skill_md_exists", skill_md.exists(), str(skill_md))
    add(checks, "frontmatter_name", "name: tradingagents-codex" in content, "")
    for section in REQUIRED_SECTIONS:
        add(checks, f"section_{section.removeprefix('## ').lower()}", section in content, section)

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    openai_text = openai_yaml.read_text(encoding="utf-8") if openai_yaml.exists() else ""
    add(checks, "openai_yaml_exists", openai_yaml.exists(), str(openai_yaml))
    add(checks, "openai_default_prompt_mentions_skill", "$tradingagents-codex" in openai_text, "")

    for script_name in REQUIRED_SCRIPTS:
        path = skill_dir / "scripts" / script_name
        add(checks, f"{script_name}_exists", path.exists(), str(path))
        if path.exists():
            try:
                add(checks, f"{script_name}_imports", import_script(path), "")
            except Exception as exc:
                add(checks, f"{script_name}_imports", False, repr(exc))
            ok, detail = run_help(path)
            add(checks, f"{script_name}_help", ok, detail)

    ok, detail = fixture_summary_test(skill_dir)
    add(checks, "summarize_fixture", ok, detail)

    if args.project:
        check_setup = skill_dir / "scripts" / "check_setup.py"
        proc = subprocess.run(
            [sys.executable, str(check_setup), "--project", args.project],
            capture_output=True,
            text=True,
            timeout=90,
        )
        add(checks, "real_project_check_setup", proc.returncode == 0, proc.stderr.strip() or proc.stdout[:300])

    valid = all(check["ok"] for check in checks)
    print(json.dumps({"valid": valid, "skill_dir": str(skill_dir), "checks": checks}, ensure_ascii=False, indent=2))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
