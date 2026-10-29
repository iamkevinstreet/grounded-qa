# live-hybrid

Model: `claude-sonnet-5-5` (anthropic). Cases: 56. Failures: 0. Run: 2026-10-29T12:25:29+00:00. Prices as of 2026-10-15.

| Measure | Value |
| --- | --- |
| abstained_correctly | 1 |
| answered | 0.8889 |
| citation_precision | 0.8246 |
| correct | 0.8889 |
| dropped | 0 |
| forbidden_hit | 0 |
| mrr | 0.6915 |
| recall_at_k | 0.8667 |
| latency_p50_ms | 2,710 |
| latency_p95_ms | 8,263 |
| cost_total_usd | 0.4698 |
| cost_per_case_usd | 0.0084 |
| failure_rate | 0 |

## By tag

| Tag | Cases | abstained_correctly | answered | citation_precision | correct | dropped | forbidden_hit | mrr | recall_at_k |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adversarial | 6 | 1 | 0.4 | 0.5333 | 0.4 | 0 | 0 | 0.09 | 0.4 |
| advice | 1 | None | 0 | None | 0 | 0 | 0 | 0 | 0 |
| direct | 35 | None | 1 | 0.8548 | 1 | 0 | 0 | 0.8333 | 1 |
| false-premise | 2 | None | 0.5 | 0.6667 | 0.5 | 0 | 0 | 0.125 | 0.5 |
| flsa | 12 | None | 1 | 0.8958 | 1 | 0 | 0 | 0.8472 | 1 |
| fmla | 24 | None | 0.9583 | 0.7899 | 0.9583 | 0 | 0 | 0.7292 | 0.9167 |
| injection | 3 | 1 | 0.5 | 0.4 | 0.5 | 0 | 0 | 0.1 | 0.5 |
| paraphrased | 5 | None | 0.6 | 0.6667 | 0.6 | 0 | 0 | 0.3 | 0.4 |
| pump | 2 | None | 1 | 1 | 1 | 0 | 0 | 1 | 1 |
| retaliation | 2 | None | 0.5 | 1 | 0.5 | 0 | 0 | 0.5 | 0.5 |
| unanswerable | 10 | 1 | None | None | None | 0 | 0 | None | None |
