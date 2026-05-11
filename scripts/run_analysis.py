#!/usr/bin/env python3
"""Run TradingAgents Codex analyses with safe defaults."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shlex
import subprocess
import sys
from pathlib import Path


DEFAULT_PROJECT = str(Path.home() / "TradingAgents_codex")
DEFAULT_ANALYSTS = "market,news,social,fundamentals"


def resolve_project(raw: str | None) -> Path:
    return Path(raw or os.environ.get("TRADINGAGENTS_PROJECT") or DEFAULT_PROJECT).expanduser().resolve()


def latest_completed_us_trading_day(today: dt.date | None = None) -> dt.date:
    """Return a conservative latest completed US trading day, ignoring holidays."""
    candidate = (today or dt.date.today()) - dt.timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate -= dt.timedelta(days=1)
    return candidate


def normalize_tickers(args: argparse.Namespace) -> list[str]:
    raw: list[str] = []
    raw.extend(args.symbols or [])
    raw.extend(args.ticker or [])
    if args.tickers:
        raw.extend(args.tickers.split(","))
    tickers = []
    for item in raw:
        for part in item.replace(",", " ").split():
            symbol = part.strip().upper()
            if symbol and symbol not in tickers:
                tickers.append(symbol)
    return tickers


def build_command(binary: Path, ticker: str, args: argparse.Namespace, analysis_date: str) -> list[str]:
    cmd = [
        str(binary),
        "codex-analyze",
        "--ticker",
        ticker,
        "--analysis-date",
        analysis_date,
        "--model",
        args.model,
        "--reasoning-effort",
        args.reasoning_effort,
        "--output-language",
        args.output_language,
        "--analysts",
        args.analysts,
        "--max-parallel",
        str(args.max_parallel),
    ]
    if not args.no_search:
        cmd.append("--search")
    if args.analysts_only:
        cmd.append("--analysts-only")
    return cmd


def display_command(cmd: list[str]) -> str:
    return "env -u NODE_OPTIONS " + " ".join(shlex.quote(part) for part in cmd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("symbols", nargs="*", help="Ticker symbols")
    parser.add_argument("--ticker", action="append", help="Ticker symbol; repeatable")
    parser.add_argument("--tickers", help="Comma-separated ticker symbols")
    parser.add_argument("--date", dest="analysis_date", help="Analysis date, YYYY-MM-DD")
    parser.add_argument("--project", help="Path to TradingAgents_codex project")
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--reasoning-effort", default="high")
    parser.add_argument("--output-language", default="Chinese")
    parser.add_argument("--analysts", default=DEFAULT_ANALYSTS)
    parser.add_argument("--max-parallel", type=int, default=2, help="TradingAgents internal role parallelism")
    parser.add_argument("--no-search", action="store_true", help="Disable live search")
    parser.add_argument("--analysts-only", action="store_true", help="Run analyst reports only, not the full chain")
    parser.add_argument("--timeout", type=int, default=3600, help="Max seconds per ticker")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    parser.add_argument("--confirm", action="store_true", help="Allow batches larger than three tickers")
    args = parser.parse_args()

    tickers = normalize_tickers(args)
    if not tickers:
        parser.error("Provide at least one ticker via positional args, --ticker, or --tickers.")

    project = resolve_project(args.project)
    binary = project / ".venv" / "bin" / "tradingagents"
    analysis_date = args.analysis_date or latest_completed_us_trading_day().isoformat()

    if len(tickers) > 3 and not args.dry_run and not args.confirm:
        print(
            f"Refusing to run {len(tickers)} tickers without --confirm. "
            "Full-chain analysis can be slow and costly. Use --dry-run to preview.",
            file=sys.stderr,
        )
        return 1

    if not project.exists():
        print(f"Project not found: {project}", file=sys.stderr)
        return 1
    if not binary.exists():
        print(f"TradingAgents CLI not found: {binary}", file=sys.stderr)
        return 1

    env = os.environ.copy()
    env.pop("NODE_OPTIONS", None)
    failures = 0

    for ticker in tickers:
        run_dir = project / "codex_runs" / ticker / analysis_date
        report = run_dir / "reports" / "complete_report.md"
        cmd = build_command(binary, ticker, args, analysis_date)
        print(f"\n[{ticker}] command:")
        print(display_command(cmd))
        print(f"[{ticker}] expected run dir: {run_dir}")
        print(f"[{ticker}] expected complete report: {report}")

        if args.dry_run:
            continue

        try:
            completed = subprocess.run(cmd, cwd=project, env=env, timeout=args.timeout)
        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT] {ticker}: exceeded {args.timeout}s. Partial artifacts may exist at {run_dir}", file=sys.stderr)
            failures += 1
            continue

        if completed.returncode != 0:
            print(f"[FAILED] {ticker}: exit code {completed.returncode}", file=sys.stderr)
            failures += 1
        else:
            print(f"[OK] {ticker}: {report}")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
