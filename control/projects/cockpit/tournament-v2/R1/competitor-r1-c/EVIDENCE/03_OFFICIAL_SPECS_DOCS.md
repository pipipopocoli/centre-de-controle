# Official Specs and Docs

Context
- This file lists official specifications used as normative references.

Problem statement
- Without normative specs, interfaces drift and replay/debug contracts become ambiguous.

Proposed design
- Anchor transport, telemetry, and remote invocation contracts to official docs.

Interfaces and contracts
- Spec record contract:
  - source_id
  - title
  - url
  - contract_area

Failure modes
- Informal docs mistaken as normative references.

Validation strategy
- Check spec/doc count >= 2.
- Verify each spec is linked from CLAIM_MATRIX.md.

Rollout/rollback
- Rollout: use these as baseline contract authorities.
- Rollback: if superseded, version-pin and document migration notes.

Risks and mitigations
- Risk: version mismatch between plan and runtime.
- Mitigation: add version field in interfaces and test gates.

Resource impact
- Minimal.

## Official docs
- SRC-D1 | OpenTelemetry Specification | https://opentelemetry.io/docs/specs/ | tracing and metrics schema.
- SRC-D2 | W3C Trace Context | https://www.w3.org/TR/trace-context/ | trace propagation across router boundaries.
- SRC-D3 | JSON-RPC 2.0 Specification | https://www.jsonrpc.org/specification | control-plane API envelope and error contracts.
