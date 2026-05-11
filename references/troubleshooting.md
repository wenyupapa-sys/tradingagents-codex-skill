# TradingAgents Codex Troubleshooting

## `NODE_OPTIONS=--use-env-proxy` failure

Symptom:

```text
node: --use-env-proxy is not allowed in NODE_OPTIONS
```

Mitigation: always clear `NODE_OPTIONS` for TradingAgents child processes. The scripts do this automatically. Manual command pattern:

```bash
env -u NODE_OPTIONS .venv/bin/tradingagents codex-analyze ...
```

## ETF fundamentals gaps

Yahoo-style fundamentals can be missing for ETFs such as QQQ. Do not invent missing balance sheet, cash flow, income statement, or insider data. Mention the limitation in the final summary.

## Missing analysis-date OHLC row

Local market artifacts may lag the requested analysis date. If the report says the latest row is the prior trading day, include that limitation and avoid treating exact analysis-date price action as known.

## Slow Chinese output

Chinese output can add a long translation stage after core analysis finishes. If the user mainly needs the decision, use `--output-language English` and summarize `portfolio_manager.json` in Chinese.

## Batch cost guard

`run_analysis.py` refuses more than three tickers unless `--confirm` is supplied. Use `--dry-run` first for larger batches.

## Timeouts

Full-chain runs can be slow. Use `--timeout` to set max seconds per ticker. Partial artifacts may still exist under `codex_runs/<TICKER>/<DATE>/`.

## Missing report JSON

If `summarize_report.py` cannot find `reports/portfolio_manager.json`, check whether the run completed. Analyst-only runs may not create a portfolio manager report.
