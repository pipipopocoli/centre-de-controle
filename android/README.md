# Cockpit Android Bootstrap (Wave21)

This module is a bootstrap for the native Android client aligned with Cockpit Cloud API.

## Scope included

- Kotlin + Compose entrypoint
- API interface skeleton for:
  - auth login
  - projects list
  - chat message post
  - wizard live endpoints
  - agentic turn endpoint
- Placeholder state holder for future WS + push integration

## Not included (Wave21)

- Full parity UI/UX with Desktop
- Voice capture pipeline
- Pixel heatmap advanced rendering
- FCM delivery worker

## Next

1. Add Gradle wrapper and Android Studio project sync.
2. Add secure token storage + refresh flow.
3. Add websocket event stream and project timeline views.

