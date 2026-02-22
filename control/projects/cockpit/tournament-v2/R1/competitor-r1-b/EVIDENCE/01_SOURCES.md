# Evidence Catalog - competitor-r1-b (Variant B)

## Coverage summary
- Primary papers: 9
- Open-source repositories: 8
- Official specs/docs: 5

## Primary papers

### P1
- Citation: Ken Thompson, "Reflections on Trusting Trust" (1984)
- Why it matters: Shows compiler and toolchain subversion risk; justifies provenance and independent verification.
- Link: https://dl.acm.org/doi/10.1145/358198.358210

### P2
- Citation: Justin Cappos et al., "A Look in the Mirror: Attacks on Package Managers" (USENIX Security 2008)
- Why it matters: Demonstrates realistic attack vectors in package/update channels.
- Link: https://www.usenix.org/legacy/event/sec08/tech/full_papers/cappos/cappos.pdf

### P3
- Citation: Justin Samuel et al., "Survivable Key Compromise in Software Update Systems" (2010)
- Why it matters: Foundation for TUF-style threshold trust and key compromise resilience.
- Link: https://theupdateframework.io/papers/survivable-key-compromise.pdf

### P4
- Citation: Santiago Torres-Arias et al., "in-toto: providing farm-to-table guarantees for bits and bytes" (USENIX Security 2019)
- Why it matters: Defines end-to-end software supply chain metadata and attestation model.
- Link: https://www.usenix.org/system/files/sec19-torres-arias.pdf

### P5
- Citation: Marc Ohm et al., "Backstabber's Knife Collection: A Review of Open Source Software Supply Chain Attacks" (2020)
- Why it matters: Catalogs attack classes and defense gaps in OSS ecosystems.
- Link: https://arxiv.org/abs/2005.09535

### P6
- Citation: Patrick Hunt et al., "ZooKeeper: Wait-free coordination for Internet-scale systems" (USENIX ATC 2010)
- Why it matters: Coordination model for distributed-like agent orchestration and leader election.
- Link: https://www.usenix.org/legacy/event/atc10/tech/full_papers/Hunt.pdf

### P7
- Citation: Diego Ongaro and John Ousterhout, "In Search of an Understandable Consensus Algorithm (Raft)" (2014)
- Why it matters: Deterministic leadership/log replication principles useful for replay-safe control planes.
- Link: https://raft.github.io/raft.pdf

### P8
- Citation: K. Mani Chandy and Leslie Lamport, "Distributed Snapshots" (ACM TOCS 1985)
- Why it matters: Durable checkpointing model for replay and incident forensics.
- Link: https://lamport.azurewebsites.net/pubs/chandy.pdf

### P9
- Citation: Benjamin H. Sigelman et al., "Dapper, a Large-Scale Distributed Systems Tracing Infrastructure" (2010)
- Why it matters: Traceability baseline for deterministic replay and auditability requirements.
- Link: https://research.google/pubs/pub36356/

## Open-source repositories

### R1
- Name: theupdateframework/python-tuf
- Why it matters: Reference implementation for TUF metadata verification and client update workflow.
- Link: https://github.com/theupdateframework/python-tuf

### R2
- Name: in-toto/in-toto
- Why it matters: Supply chain layout and link metadata tooling.
- Link: https://github.com/in-toto/in-toto

### R3
- Name: sigstore/cosign
- Why it matters: Signing and transparency-backed verification for artifacts and OCI.
- Link: https://github.com/sigstore/cosign

### R4
- Name: slsa-framework/slsa-github-generator
- Why it matters: Practical provenance generation patterns aligned with SLSA.
- Link: https://github.com/slsa-framework/slsa-github-generator

### R5
- Name: google/osv-scanner
- Why it matters: Vulnerability scanning against OSV for lockfile and dependency policy.
- Link: https://github.com/google/osv-scanner

### R6
- Name: aquasecurity/trivy
- Why it matters: SBOM, vuln, and misconfig scanning across artifacts and containers.
- Link: https://github.com/aquasecurity/trivy

### R7
- Name: anchore/syft
- Why it matters: SBOM generation used in build/install attestations.
- Link: https://github.com/anchore/syft

### R8
- Name: guacsec/guac
- Why it matters: Graphing attestations/SBOM/provenance for investigative and policy queries.
- Link: https://github.com/guacsec/guac

## Official specs/docs

### D1
- Name: SLSA v1.0 specification
- Why it matters: Defines build provenance maturity and requirements.
- Link: https://slsa.dev/spec/v1.0/

### D2
- Name: The Update Framework (TUF) specification
- Why it matters: Canonical secure update metadata and client verification model.
- Link: https://theupdateframework.github.io/specification/latest/

### D3
- Name: SPDX 2.3 specification
- Why it matters: Standard SBOM format and license/security metadata exchange.
- Link: https://spdx.github.io/spdx-spec/v2.3/

### D4
- Name: CycloneDX 1.6 specification
- Why it matters: Alternative SBOM format with vuln and dependency semantics.
- Link: https://cyclonedx.org/specification/overview/

### D5
- Name: OCI Distribution specification
- Why it matters: Artifact transport contract for signed skill bundles.
- Link: https://github.com/opencontainers/distribution-spec/blob/main/spec.md
