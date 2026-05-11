# TradingAgents Codex Skill

Agent Skill for running a local TradingAgents Codex fork as a repeatable stock and ETF research workflow.

The skill wraps:

- setup validation for a local `TradingAgents_codex` checkout
- dry-run command construction
- full-chain `tradingagents codex-analyze` runs
- report summarization from `portfolio_manager.json`

## Requirements

- Python 3.11+
- A local TradingAgents Codex project with an installed virtual environment
- A working `.venv/bin/tradingagents` CLI inside that project
- Codex CLI available to the TradingAgents project when live analysis is run

The skill does not vendor TradingAgents itself. Point it at your local project with `TRADINGAGENTS_PROJECT` or `--project`.

## Installation

For Codex:

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/wenyupapa-sys/tradingagents-codex-skill.git ~/.codex/skills/tradingagents-codex
```

For Claude Code:

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/wenyupapa-sys/tradingagents-codex-skill.git ~/.claude/skills/tradingagents-codex
```

Configure your TradingAgents project path:

```bash
export TRADINGAGENTS_PROJECT="$HOME/TradingAgents_codex"
```

## Usage

Validate setup:

```bash
python3 ~/.codex/skills/tradingagents-codex/scripts/check_setup.py
```

Preview a run:

```bash
python3 ~/.codex/skills/tradingagents-codex/scripts/run_analysis.py \
  --ticker QQQ --ticker TSLA \
  --date 2026-05-08 \
  --output-language English \
  --dry-run
```

Run full analysis:

```bash
python3 ~/.codex/skills/tradingagents-codex/scripts/run_analysis.py \
  --ticker QQQ \
  --date 2026-05-08 \
  --model gpt-5.5 \
  --reasoning-effort high \
  --output-language English
```

Summarize a completed run:

```bash
python3 ~/.codex/skills/tradingagents-codex/scripts/summarize_report.py \
  --ticker QQQ \
  --date 2026-05-08
```

## Notes

- Outputs are research summaries, not investment advice.
- The default project path is `~/TradingAgents_codex`.
- Live search is enabled by default in `run_analysis.py`; pass `--no-search` to disable it.
- The helper scripts clear `NODE_OPTIONS` for child TradingAgents processes to avoid Node proxy-option failures.

## License

MIT
