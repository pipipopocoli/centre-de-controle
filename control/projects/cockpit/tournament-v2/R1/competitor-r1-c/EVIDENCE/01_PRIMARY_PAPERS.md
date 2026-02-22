# Primary Papers (Variant C Router Orchestration)

Context
- This file lists primary research papers used by competitor-r1-c.
- IDs are used in claim mapping and design docs.

Problem statement
- Router/orchestration plans often use folklore patterns without primary evidence.
- We need source-backed architecture choices for durability, scheduling, fairness, and replay.

Proposed design
- Use a curated paper set with direct relevance to distributed orchestration.
- Attach each source to concrete claims in CLAIM_MATRIX.md.

Interfaces and contracts
- Source record contract:
  - source_id
  - title
  - year
  - url
  - relevance_to_variant_c

Failure modes
- Broken links or weak relevance.
- Over-citation with no claim mapping.

Validation strategy
- Check source count >= 8.
- Check every source_id appears in CLAIM_MATRIX.md.

Rollout/rollback
- Rollout: start with this baseline set.
- Rollback: if one source is invalid, mark ASSUMPTION and replace with an equivalent primary source.

Risks and mitigations
- Risk: paper is too generic.
- Mitigation: keep explicit relevance note tied to router/orchestration.

Resource impact
- Low authoring overhead; high design confidence gain.

## Source list
- SRC-P1 | Leslie Lamport | Time, Clocks, and the Ordering of Events in a Distributed System | 1978 | https://lamport.azurewebsites.net/pubs/time-clocks.pdf | Basis for deterministic ordering and replay stamps.
- SRC-P2 | Giuseppe DeCandia et al | Dynamo: Amazon's Highly Available Key-value Store | 2007 | https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf | Failure handling and always-on service trade-offs.
- SRC-P3 | Mike Burrows | The Chubby Lock Service for Loosely-Coupled Distributed Systems | 2006 | https://research.google/pubs/the-chubby-lock-service-for-loosely-coupled-distributed-systems/ | Coordination and lock semantics for orchestrator leadership.
- SRC-P4 | Jeffrey Dean and Sanjay Ghemawat | MapReduce: Simplified Data Processing on Large Clusters | 2004 | https://research.google/pubs/mapreduce-simplified-data-processing-on-large-clusters/ | Task partitioning and retry model inspiration.
- SRC-P5 | Benjamin H. Sigelman et al | Dapper, a Large-Scale Distributed Systems Tracing Infrastructure | 2010 | https://research.google/pubs/dapper-a-large-scale-distributed-systems-tracing-infrastructure/ | Traceability contracts for multi-agent execution.
- SRC-P6 | Jeffrey Dean and Luiz Andre Barroso | The Tail at Scale | 2013 | https://research.google/pubs/the-tail-at-scale/ | Tail latency mitigation for routing and fallback tiers.
- SRC-P7 | James C. Corbett et al | Spanner: Google's Globally-Distributed Database | 2012 | https://research.google/pubs/spanner-googles-globally-distributed-database-2/ | Consistency and transactional boundaries.
- SRC-P8 | Diego Ongaro and John Ousterhout | In Search of an Understandable Consensus Algorithm (Raft) | 2014 | https://raft.github.io/raft.pdf | Understandable consensus and leader election model.
- SRC-P9 | Jay Kreps et al | Kafka: A Distributed Messaging System for Log Processing | 2011 | https://www.microsoft.com/en-us/research/wp-content/uploads/2017/09/Kafka.pdf | Queue durability and log-based replay strategy.
- SRC-P10 | Malte Schwarzkopf et al | Omega: Flexible, Scalable Schedulers for Large Compute Clusters | 2013 | https://research.google/pubs/omega-flexible-scalable-schedulers-for-large-compute-clusters/ | Multi-scheduler fairness and conflict handling.
