---
name: tradingagents-codex
description: Run the local TradingAgents Codex fork for multi-agent stock and ETF research. Use when the user asks to analyze tickers with TradingAgents, run codex-analyze, batch stock/ETF research, summarize TradingAgents reports, validate the TradingAgents Codex setup, or turn QQQ/TSLA-style full-chain analysis into a repeatable workflow.
---

# TradingAgents Codex

## Overview

Use this skill to run and summarize a local `TradingAgents_codex` project as an engineering workflow. It wraps setup checks, dry-run command construction, full-chain analysis runs, and report summarization.

Default local project:

```bash
~/TradingAgents_codex
```

Override it with `--project` or `TRADINGAGENTS_PROJECT`.

## Triggers

Use this skill for requests like:

- "run TradingAgents for QQQ"
- "analyze TSLA with all agents"
- "run codex-analyze"
- "summarize a TradingAgents report"
- "validate the TradingAgents Codex CLI"
- "batch stock/ETF analysis"
- "compare QQQ and TSLA TradingAgents output"

## Workflow

1. Identify tickers, analysis date, output language, and whether the user wants full-chain or `--analysts-only`.
2. Run setup validation before real analysis unless it was validated in the current session:

```bash
SKILL_DIR="${CLAUDE_SKILL_DIR:-${CODEX_HOME:-$HOME/.codex}/skills/tradingagents-codex}"
python3 "$SKILL_DIR/scripts/check_setup.py"
```

3. Dry-run the command when the run is expensive, batched, or date-sensitive:

```bash
SKILL_DIR="${CLAUDE_SKILL_DIR:-${CODEX_HOME:-$HOME/.codex}/skills/tradingagents-codex}"
python3 "$SKILL_DIR/scripts/run_analysis.py" \
  --ticker QQQ --ticker TSLA \
  --date 2026-05-08 \
  --output-language English \
  --dry-run
```

4. Run full-chain analysis. Tickers run sequentially; `--max-parallel` is passed through to TradingAgents for internal role parallelism.

```bash
SKILL_DIR="${CLAUDE_SKILL_DIR:-${CODEX_HOME:-$HOME/.codex}/skills/tradingagents-codex}"
python3 "$SKILL_DIR/scripts/run_analysis.py" \
  --ticker QQQ --ticker TSLA \
  --date 2026-05-08 \
  --model gpt-5.5 \
  --reasoning-effort high \
  --output-language English \
  --confirm
```

5. Summarize final portfolio decisions from `reports/portfolio_manager.json`:

```bash
SKILL_DIR="${CLAUDE_SKILL_DIR:-${CODEX_HOME:-$HOME/.codex}/skills/tradingagents-codex}"
python3 "$SKILL_DIR/scripts/summarize_report.py" \
  --ticker QQQ \
  --date 2026-05-08
```

## Defaults

- Model: `gpt-5.5`
- Reasoning effort: `high`
- Analysts: `market,news,social,fundamentals`
- Search: enabled
- Output language: `Chinese`
- Per-ticker timeout: 3600 seconds
- Latest date fallback: previous likely completed US trading day, skipping weekends

For speed, prefer `--output-language English` and provide the user a Chinese summary. Chinese output can spend substantial time translating each role report.

## Safety

- Treat outputs as research summaries, not investment advice.
- Never place trades, send orders, or connect brokerage execution from this skill.
- Do not invent missing prices, social data, ETF fundamentals, or latest OHLC rows.
- Mention known data gaps, especially ETF fundamentals and missing analysis-date market rows.
- Use `--dry-run` before large batches. The runner requires `--confirm` for more than three tickers.
- Always clear `NODE_OPTIONS` for child TradingAgents/Codex CLI commands; this project has a known `--use-env-proxy` failure.

## Scripts

- `scripts/check_setup.py`: validates project path, virtualenv CLI, required flags, UTF-8 locale, and `NODE_OPTIONS` workaround.
- `scripts/run_analysis.py`: builds and runs `tradingagents codex-analyze` commands with dry-run, timeout, and batch confirmation.
- `scripts/summarize_report.py`: reads `portfolio_manager.json` and emits Chinese Markdown or JSON summary.
- `scripts/quick_validate.py`: validates the skill structure and scripts without running live analysis.

## References

Read `references/workflow.md` for command examples and operational choices. Read `references/troubleshooting.md` for known failures and mitigations.
