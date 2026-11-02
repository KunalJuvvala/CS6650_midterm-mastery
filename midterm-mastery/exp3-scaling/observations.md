# Experiment 3: When and how well does the service scale under load?

## Question
Under rising load, when do the gateway and backend scale out, what limits throughput, and
what do users see while scaling happens?

## Setup
| Changed | Locust users over time: 5 -> 15 -> 40 -> 5 (3-minute steps, 12 minutes total) |
|---|---|
| Kept fixed | `size-1k.txt`, 0% loss, default scaling (gateway: 100 requests/min per task; backend: 60% average CPU; 2-4 tasks each; 60 s scale-out / 120 s scale-in cooldown), `max_inflight` = 4, `backend_workers` = 8 |
| Tools | `scripts/locustfile.py` (StepLoad shape), ECS service Events, chart from `locust_stats_history.csv` |

## Prediction (written before running)
One gateway task runs at most 4 downloads at once, and each takes at least ~2 s, so one
task handles about **2 requests/s**. Two tasks = ~4 req/s. Each user sends about one
request every ~3 s, so ~12 users should fill 2 gateway tasks. The backend does very little
CPU work per request, so it may never scale.

## Results
Test ran 00:30:56 - 00:42:56 (UTC-5) on November 2, 2026.

| Phase | Users | Throughput | Requests | 503 failures | Gateway tasks | Backend tasks |
|---|---|---|---|---|---|---|
| 0-3 min | 5 | ~1.6 req/s | 284 | 0 (0%) | 2 | 2 |
| 3-6 min | 15 | **flat at 4.0 req/s** | 698 | 0 (0%) | 2 | 2 |
| 6-9 min | 40 | ~5.5 req/s total, ~1.6/s of them 503 | 984 | **276 (28%)** | 2 -> 3 at 00:39 | 2 |
| 9-12 min | 5 | ~1.6 req/s | 298 | 0 (0%) | 3 -> 4 at 00:42 | 2 |
| **Total** | | 3.16 req/s average | **2,279** | **278 (12.2%)** | | |

Response times overall: median 3.1 s, p95 7.0 s, max 7.2 s, min 2.1 s.

Chart: `load_timeline.png`. Screenshots: `screenshots/` (gateway and backend ECS Events).

## Observations
- **The predicted ceiling showed up exactly.** At 15 users, throughput flattened at
  **4.0 requests/s**: 2 gateway tasks x 4 in-flight slots / ~2 s per download. Requests
  started queuing (median rose from 2.1 s to ~2.6 s) but stayed under the 5 s queue limit,
  so no errors yet.
- **Past the ceiling, users got 503s.** At 40 users, about 28% of requests waited 5 s for
  a free slot and were rejected with 503 "gateway is busy." That is why p95 jumped to
  ~7 s: 5 s of queueing plus a 2 s download.
- **Scaling was too slow to help.** Load jumped at 00:36:56. The gateway's first scale-out
  (2 -> 3 tasks) came at 00:39, about 2 minutes later, and the 503s continued. The second
  scale-out (3 -> 4) came at 00:42, after the load had already dropped back to 5 users.
  The scaler was reacting to the past.
- **The backend never scaled.** It stayed at 2 tasks the whole time. Its Events show no
  scaling activity during the test, because sending a 1 KB file barely uses CPU, so its
  60% CPU target was never reached.

## What it reveals about the service
- The gateway's real bottleneck is **`max_inflight` x the 2 s quiet timeout**, not CPU or
  network. Each task is mostly waiting, yet it can only serve ~2 requests/s.
- Target tracking on requests per target needs several minutes of CloudWatch data plus
  task start-up time, so short spikes are absorbed by **rejecting users**, not by scaling.
- **CPU is the wrong scaling metric for the backend**: it does little computation, so CPU
  stays low even when the system is overloaded (and, per Experiment 2, it drops requests
  from its 32-slot queue long before CPU rises).
- Improvements to suggest: raise `max_inflight` (the tasks are idle while waiting), shorten
  the 2 s quiet timeout, scale the gateway on a lower requests-per-target value, shorten
  the scale-out cooldown, and scale the backend on a load signal rather than CPU.

## Limitations
3-minute steps are short for target tracking; scale-in was not observed because the test
ended 1 minute after the last scale-out.
