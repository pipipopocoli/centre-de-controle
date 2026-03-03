# Android Native App Blueprint (Cockpit)

Date: 2026-03-03

## Wave21 bootstrap status

- Bootstrap module added under `/Users/oliviercloutier/Desktop/Cockpit/android/`.
- Includes:
  - Compose `MainActivity`
  - Retrofit interface for auth/projects/chat/wizard/agentic endpoints
  - Gradle project skeleton (`settings.gradle`, root/app `build.gradle`)
- Not yet delivered:
  - full parity screens
  - websocket live stream
  - FCM worker delivery path
  - voice capture UI

## Stack

- Kotlin
- Jetpack Compose
- Ktor/OkHttp client
- Room (cache)
- EncryptedSharedPreferences (tokens)
- FCM push notifications

## Screens (Parity target)

1. Login
2. Projects list + project switch
3. Chat (global + thread)
4. Agents grid
5. State
6. Roadmap
7. Decisions
8. Wizard live controls (start/run/stop)
9. Runs viewer
10. BMAD docs viewer/editor

## Networking

- REST for CRUD
- WebSocket for real-time events (`/v1/projects/{id}/events`)
- Reconnect strategy:
  - exponential backoff
  - full re-sync on reconnect

## Security

- JWT access + refresh
- RBAC-aware UI (hide/disable write actions for viewer)
- No API keys embedded in APK

## Push

- Register device with `POST /v1/devices/register`
- Route all critical and workflow events via FCM
- Client side throttle and channel grouping to avoid notification storm
