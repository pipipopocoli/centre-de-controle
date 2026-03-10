Objective
- Improve OpenRouter runtime reliability, degraded honesty, and provider diagnostics.

Constraints
- Do not change public chat route shapes.
- Keep direct and room semantics separate.

Output
- Code changes in rust runtime and frontend diagnostics only where required.

Done
- Direct and room degraded paths are honest and testable.
