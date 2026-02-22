# Open Source Repositories

Context
- This file lists open source implementations that informed execution design choices.

Problem statement
- Architecture plans need practical reference points, not only papers.

Proposed design
- Capture mature repos for orchestration, queues, tracing, and workflow durability.

Interfaces and contracts
- Repo record contract:
  - source_id
  - repo
  - url
  - relevance
  - maturity signal

Failure modes
- Picking a repo that is popular but irrelevant.
- Treating repo behavior as standard without policy adaptation.

Validation strategy
- Check repo count >= 6.
- Check every repo has a mapped claim in CLAIM_MATRIX.md.

Rollout/rollback
- Rollout: use repos as design references only in R1.
- Rollback: if unsuitable, demote to ASSUMPTION and replace source.

Risks and mitigations
- Risk: overfitting plan to one ecosystem.
- Mitigation: keep multi-repo comparison per major subsystem.

Resource impact
- Low research overhead, medium documentation overhead.

## Repo shortlist
- SRC-R1 | temporalio/temporal | https://github.com/temporalio/temporal | Durable workflow execution and deterministic replay boundaries | strong release cadence.
- SRC-R2 | apache/kafka | https://github.com/apache/kafka | Log-based queue model and consumer lag controls | very high adoption.
- SRC-R3 | nats-io/nats-server | https://github.com/nats-io/nats-server | Lightweight pubsub and request-reply patterns for orchestration edges | strong operational simplicity.
- SRC-R4 | argo-workflows/argo-workflows | https://github.com/argoproj/argo-workflows | DAG workflow scheduling and retry policies | production use in CI/data stacks.
- SRC-R5 | ray-project/ray | https://github.com/ray-project/ray | Distributed task scheduling and backpressure concepts | broad scale usage.
- SRC-R6 | kubernetes/kubernetes | https://github.com/kubernetes/kubernetes | Controller loops and reconciliation model | ecosystem standard.
- SRC-R7 | open-telemetry/opentelemetry-collector | https://github.com/open-telemetry/opentelemetry-collector | Unified telemetry pipeline and exporter contracts | strong observability alignment.
- SRC-R8 | redis/redis | https://github.com/redis/redis | Fast queue primitives and circuit breaker cache patterns | widely deployed operational component.
