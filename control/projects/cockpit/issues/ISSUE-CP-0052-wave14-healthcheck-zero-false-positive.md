# ISSUE-CP-0052 - Wave14 Healthcheck Zero False Positive

- Owner: victor
- Phase: Plan
- Status: Open

## Objective
Reduce operational false positives in healthchecks while keeping true failures visible.

## Scope (In)
- `scripts/auto_mode_healthcheck.py`
- `app/services/auto_mode.py`
- `tests/verify_auto_mode_healthcheck.py`
- `tests/verify_wave07_control_gates.py`

## Done (Definition)
- [ ] False-positive scenarios covered by deterministic tests.
- [ ] Healthcheck semantics document clear reasons for degraded vs healthy.
- [ ] Alert quality improved without muting true incidents.
- [ ] Operator guidance updated for pulse cadence expectations.

## Constraints
- no silent failure masking
- no tournament side effects
