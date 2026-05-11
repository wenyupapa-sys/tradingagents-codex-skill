#!/usr/bin/env python3
"""Summarize a TradingAgents portfolio manager report."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


DEFAULT_PROJECT = str(Path.home() / "TradingAgents_codex")


def resolve_project(raw: str | None) -> Path:
    return Path(raw or os.environ.get("TRADINGAGENTS_PROJECT") or DEFAULT_PROJECT).expanduser().resolve()


def find_run_dir(args: argparse.Namespace) -> Path:
    if args.run_dir:
        return Path(args.run_dir).expanduser().resolve()
    if not args.ticker or not args.date:
        raise SystemExit("Provide --run-dir or both --ticker and --date.")
    return resolve_project(args.project) / "codex_runs" / args.ticker.upper() / args.date


def load_report(run_dir: Path) -> tuple[dict[str, Any], Path]:
    report_json = run_dir / "reports" / "portfolio_manager.json"
    if not report_json.exists():
        existing = []
        if run_dir.exists():
            existing = [str(path.relative_to(run_dir)) for path in sorted(run_dir.rglob("*")) if path.is_file()]
        raise FileNotFoundError(
            f"Missing {report_json}. Existing artifacts: {existing[:40]}"
        )
    with report_json.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{report_json} must contain a JSON object")
    return data, report_json


def require(data: dict[str, Any], keys: list[str]) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise KeyError(f"portfolio_manager.json missing keys {missing}; available keys: {sorted(data.keys())}")


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def render_markdown(data: dict[str, Any], run_dir: Path) -> str:
    require(data, ["rating", "summary"])
    horizon = data.get("time_horizon") or data.get("horizon") or ""
    positioning = data.get("positioning") if isinstance(data.get("positioning"), dict) else {}
    report = run_dir / "reports" / "complete_report.md"

    lines = [
        f"# {data.get('ticker', '')} TradingAgents summary",
        "",
        f"- Analysis date: {data.get('analysis_date', '')}",
        f"- Rating: {data.get('rating', '')}",
    ]
    if horizon:
        lines.append(f"- Horizon: {horizon}")
    lines.extend(["", "## Summary", str(data.get("summary", ""))])

    if positioning:
        lines.extend(["", "## Positioning"])
        for key in ("entry", "size", "stop", "take_profit"):
            if key in positioning:
                lines.append(f"- {key}: {positioning[key]}")

    reasons = as_list(data.get("top_reasons"))
    if reasons:
        lines.extend(["", "## Top reasons"])
        lines.extend(f"- {item}" for item in reasons)

    risks = as_list(data.get("top_risks"))
    if risks:
        lines.extend(["", "## Top risks"])
        lines.extend(f"- {item}" for item in risks)

    lines.extend(["", f"Complete report: {report}"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", help="Path to TradingAgents_codex project")
    parser.add_argument("--ticker", help="Ticker symbol")
    parser.add_argument("--date", help="Analysis date, YYYY-MM-DD")
    parser.add_argument("--run-dir", help="Direct run directory")
    parser.add_argument("--output", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    try:
        run_dir = find_run_dir(args)
        data, report_json = load_report(run_dir)
        if args.output == "json":
            print(json.dumps({"run_dir": str(run_dir), "report_json": str(report_json), "portfolio_manager": data}, ensure_ascii=False, indent=2))
        else:
            print(render_markdown(data, run_dir), end="")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
