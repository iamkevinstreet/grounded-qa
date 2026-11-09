# live-keyword

Model: `claude-sonnet-5-5` (anthropic). Cases: 56. Failures: 0. Run: 2026-11-09T04:02:24+00:00. Prices as of 2026-10-15.

| Measure | Value |
| --- | --- |
| abstained_correctly | 1 |
| answered | 0.8889 |
| citation_precision | 0.8063 |
| correct | 0.8889 |
| dropped | 0 |
| forbidden_hit | 0.0179 |
| judge_agrees | 0.925 |
| judge_correct | 0.925 |
| judge_cost_usd | 0.004 |
| judge_score | 1.925 |
| mrr | 0.6363 |
| recall_at_k | 0.8667 |
| latency_p50_ms | 4,325 |
| latency_p95_ms | 8,510 |
| cost_total_usd | 0.466 |
| cost_per_case_usd | 0.0083 |
| failure_rate | 0 |

## By tag

| Tag | Cases | abstained_correctly | answered | citation_precision | correct | dropped | forbidden_hit | judge_agrees | judge_correct | judge_cost_usd | judge_score | mrr | recall_at_k |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adversarial | 6 | 1 | 0.4 | 0.5417 | 0.4 | 0 | 0.1667 | 1 | 1 | 0.0053 | 2 | 0.09 | 0.4 |
| advice | 1 | None | 0 | None | 0 | 0 | 1 | None | None | None | None | 0 | 0 |
| direct | 35 | None | 1 | 0.8405 | 1 | 0 | 0 | 0.9429 | 0.9429 | 0.0038 | 1.9429 | 0.7695 | 1 |
| false-premise | 2 | None | 0.5 | 0.3333 | 0.5 | 0 | 0 | 1 | 1 | 0.0056 | 2 | 0.125 | 0.5 |
| flsa | 12 | None | 1 | 0.8611 | 1 | 0 | 0 | 1 | 1 | 0.0036 | 2 | 0.8042 | 1 |
| fmla | 24 | None | 0.9583 | 0.7754 | 0.9583 | 0 | 0 | 0.8696 | 0.8696 | 0.0043 | 1.8696 | 0.6472 | 0.9167 |
| injection | 3 | 1 | 0.5 | 0.75 | 0.5 | 0 | 0 | 1 | 1 | 0.005 | 2 | 0.1 | 0.5 |
| paraphrased | 5 | None | 0.6 | 0.5833 | 0.6 | 0 | 0 | 0.6667 | 0.6667 | 0.0059 | 1.6667 | 0.25 | 0.4 |
| pump | 2 | None | 1 | 1 | 1 | 0 | 0 | 1 | 1 | 0.0034 | 2 | 1 | 1 |
| retaliation | 2 | None | 0.5 | 1 | 0.5 | 0 | 0 | 1 | 1 | 0.0031 | 2 | 0.5 | 0.5 |
| unanswerable | 10 | 1 | None | None | None | 0 | 0 | None | None | None | None | None | None |
