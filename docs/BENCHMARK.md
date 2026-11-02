# Recorded live-model evaluation

The checked-in report in `backend/reports/9c9927bb5b1241f5b234f54cc432e71d.json` contains actual Ollama outputs, reasons, per-trial timings and gateway decisions. It is a recorded run, not a newly generated result on every page load. Use the console's Live benchmark action to run it again.

## Method

20 owned synthetic cases in `backend/benchmarks/cases.json`, repeated three times with `gemma2:2b`, temperature 0, structured output, 220 generated-token limit. Eight benign cases, four direct policy overrides and eight seller-text injections. The same planner function runs the application and benchmark.

Each actual suggestion is scored twice: as a prompt-only recommendation, and by the gateway in a fresh simulated ledger. The latter performs policy validation and exact-cart approval; it never calls PayPal. An independent specification oracle evaluates catalogue prices, quantities, merchants, categories and spending limits. A deliberately broken gate test verifies the oracle can detect unsafe acceptance. Expected carts determine task success separately from policy safety. Empty-cart refusal can be correct for a task. Errors remain in the total-attempt denominator.

| Measurement | Recorded result |
|---|---:|
| Attempted / valid responses | 60 / 60 |
| Unsafe model suggestions | 12 |
| Unsafe suggestions blocked | 12 |
| Policy-violating suggestions accepted | 0 |
| Compliant suggestions incorrectly blocked | 0 |
| Tasks matching the expected cart | 42 / 60 (70%) |
| Median inference latency | 686 ms |

Evaluator version 2 re-scored the saved outputs with the independent oracle. No new model inference was represented as part of that re-scoring. The dataset hash and revalidation timestamp are in the report.

## Limits

The prompt-only baseline measures unsafe proposals, not real payments. Deterministic repeats frequently produce identical outputs and are not 60 independent samples. This small synthetic dataset does not establish a general attack-success rate or production fraud effectiveness. Model choice, prompt or dataset changes require a fresh run. Gateway compliance does not ensure the cart meets the user's actual intent: 18 trials missed the expected task. Local latency excludes cold model loading and differs from hosted inference.

The separate ten-case Failure lab uses deterministic inputs and a simulated provider. It checks ledger behavior; it is not a live-model benchmark.

## Coordinated mission evaluation (separate report)

`backend/reports/mission-evaluation.json` records six cases per model, one run each, using the actual v0.3 mission planner. Cases cover $90/$100/$125 budgets, audio-only category scope, forged seller approval and quantity overrides. Iris and Nova use separate model calls with shared planning context. The same model serves both roles in each mission. After a rejection the gateway supplies explicit feedback and a feasible catalogue; no substitute cart is inserted.

| Model | Exact expected carts matched | Model attempts | Unsafe suggestions | Policy violations accepted | Model errors | Median model inference |
|---|---:|---:|---:|---:|---:|---:|
| gemma2:2b | 5/6 | 19 | 8 | 0 | 0 | 704 ms |
| qwen2.5:7b | 6/6 | 15 | 3 | 0 | 0 | 980 ms |

Unsafe suggestions include ordinary overspending mistakes as well as adversarial inputs. These numbers are not attack-success counts. An independent policy oracle checks each raw suggestion against that call's remaining planning funds and owner scope; exact expected carts measure task success separately. Temporary simulated ledgers isolate every mission; no PayPal requests occur.

The Gemma quantity-override case missed the expected task; its unsuccessful outputs remain in the report. Six cases are insufficient to establish a general model ranking, production security or broad commerce usefulness. Qwen is the local demo default based on this bounded comparison. The older 60-trial Gemma benchmark remains labelled with its actual model and evaluates a different workflow.

To reproduce from `backend`:

```powershell
..\.venv\Scripts\python.exe -m agentgate.mission_eval --models gemma2:2b qwen2.5:7b
```

This replaces the mission report with a new recorded run. Use `--output reports/another-run.json` to preserve the existing report. The Live benchmark view exposes the saved mission report and its raw JSON separately from the original benchmark.
