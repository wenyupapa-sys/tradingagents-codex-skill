# TradingAgents Codex Workflow

## Project discovery

Use this order:

1. User-provided `--project`
2. `TRADINGAGENTS_PROJECT`
3. `~/TradingAgents_codex`

Run setup validation before a live analysis:

```bash
SKILL_DIR="${CLAUDE_SKILL_DIR:-${CODEX_HOME:-$HOME/.codex}/skills/tradingagents-codex}"
python3 "$SKILL_DIR/scripts/check_setup.py"
```

## Full-chain vs analysts-only

Use full-chain for portfolio decisions. It runs analyst reports, bull/bear debate, research manager, trader, risk roles, and portfolio manager.

Use `--analysts-only` for a cheaper smoke test or when the user only wants raw analyst perspectives.

## Date choice

If the user does not provide a date, `run_analysis.py` uses the previous likely completed US trading day and skips weekends. It does not model US exchange holidays.

## Dry run

Use `--dry-run` to print the exact command and expected output paths without API calls:

```bash
SKILL_DIR="${CLAUDE_SKILL_DIR:-${CODEX_HOME:-$HOME/.codex}/skills/tradingagents-codex}"
python3 "$SKILL_DIR/scripts/run_analysis.py" \
  --ticker QQQ --ticker TSLA --dry-run
```

## Live run

Use English output for speed, then summarize in Chinese:

```bash
SKILL_DIR="${CLAUDE_SKILL_DIR:-${CODEX_HOME:-$HOME/.codex}/skills/tradingagents-codex}"
python3 "$SKILL_DIR/scripts/run_analysis.py" \
  --ticker QQQ --ticker TSLA \
  --date 2026-05-08 \
  --output-language English \
  --confirm
```

Use Chinese output when the user explicitly needs all role reports translated:

```bash
SKILL_DIR="${CLAUDE_SKILL_DIR:-${CODEX_HOME:-$HOME/.codex}/skills/tradingagents-codex}"
python3 "$SKILL_DIR/scripts/run_analysis.py" \
  --ticker QQQ \
  --date 2026-05-08 \
  --output-language Chinese
```

## Report layout

Expected run directory:

```text
<project>/codex_runs/<TICKER>/<YYYY-MM-DD>/
```

Final decision:

```text
<run-dir>/reports/portfolio_manager.json
```

Complete Markdown report:

```text
<run-dir>/reports/complete_report.md
```

## Summarization

```bash
SKILL_DIR="${CLAUDE_SKILL_DIR:-${CODEX_HOME:-$HOME/.codex}/skills/tradingagents-codex}"
python3 "$SKILL_DIR/scripts/summarize_report.py" \
  --ticker TSLA \
  --date 2026-05-08
```

Use `--output json` for automation.
