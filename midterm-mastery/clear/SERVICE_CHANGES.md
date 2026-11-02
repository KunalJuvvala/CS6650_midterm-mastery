# Changes made to the service

The service lives in my fork: https://github.com/KunalJuvvala/file-transfer-playservice
None of its Go files are copied here.

## Code changes
None. I did not edit any Go code, Dockerfiles, or Terraform files. All experiments used
the original service.

## Settings changed
Only through the deploy script's `--var` flag (`scripts/deploy.sh --yes --skip-build --var NAME=VALUE`):

| Setting | Values used | Experiment |
|---|---|---|
| `backend_send_loss` | 0, 10, 20 | Experiment 1 (Experiments 2 and 3 used 0) |

Everything else stayed at the defaults in `terraform/variables.tf`: `backend_recv_loss` = 0,
`max_inflight` = 4, `backend_workers` = 8, gateway and backend 2-4 tasks, gateway scaling
target 100 requests/min per task, backend scaling target 60% CPU.

## Code I read to explain the results
- `transfer-client/udp/udp-client.go`: 2 s quiet timeout, 5 OPEN attempts, 5 RETY rounds,
  65,536-chunk limit.
- `transfer-server/protocol/server.go`: 8 workers with a 32-message queue that drops
  messages when full, and `handleRetry`, which re-downloads the whole file from S3 for
  every single-chunk retry.
- `transfer-frontend/gateway/gateway.go`: `max_inflight` semaphore and the 5 s queue wait
  before a 503.
