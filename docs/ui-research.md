# UI Research - Paper Ops (Recommended)

## Goals
- Build a mission-control UI that feels intentional, calm, and readable.
- Improve hierarchy and scan-ability for roadmap, agents, and chat.
- Keep it offline-first and fast (no heavy assets, no external calls).
- Work on desktop + acceptable on smaller screens.

## Constraints
- Local-first data (no remote dependencies).
- PySide6 QSS styling, no CSS frameworks.
- Avoid generic "dashboard" look.
- Preserve layout structure: sidebar / roadmap / agents grid / chat.

## Directions (3)

### 1) Paper Ops (Recommended)
Editorial, warm, calm. Think printed ops binder + clean UI.
- Background: warm off-white, soft surfaces.
- Accent: cobalt blue for actions + focus.
- Status colors: amber (warning), teal (success), red (blocked).
- Typography: IBM Plex Sans for UI, Plex Mono for metrics.

### 2) Signal Grid
Industrial mission-control. High contrast panels, sharp edges.
- Darker graphite surfaces + bright neon accents (orange/teal).
- Strong grid lines, visible separators, dense metrics.
- Best for power users, but can feel heavy.

### 3) Orbit Minimal
Cool gradients + soft glass surfaces, minimal chrome.
- Subtle gradients, low-contrast panels, floating cards.
- Modern and sleek but risks feeling generic.

## Paper Ops Tokens (Proposed)

### Colors
- `--bg`: #F6F3EE (warm off-white)
- `--surface`: #FFFFFF
- `--surface-2`: #F0ECE6
- `--text`: #1C1C1C (ink)
- `--muted`: #5E6167
- `--border`: #D9D3C8
- `--accent`: #2C5DFF (cobalt)
- `--warn`: #F2A94A (amber)
- `--ok`: #23A6A6 (teal)
- `--danger`: #C94B4B

### Typography
- Primary UI: IBM Plex Sans (Regular/Medium/Semibold)
- Monospace: IBM Plex Mono (metrics, ids, code)

### Spacing Scale
- 4, 8, 12, 16, 24, 32
- Cards: padding 12-16
- Panels: padding 16-24

### Layout Intent
- Sidebar: solid surface with clear separation (border + subtle shade).
- Roadmap: horizontal card, strong section headers.
- Agents grid: cards with crisp borders and bold phase/status.
- Chat: calm list, mono timestamps, minimal chrome.

### Motion
- Page load: subtle fade + 6px slide-up (200-250ms).
- No continuous animations.
- Micro feedback: hover darken for buttons only.

## Do / Dont
Do:
- Use strong hierarchy (titles > labels > details).
- Keep cards clean with clear borders and spacing.
- Use cobalt only for primary actions and focus states.

Dont:
- No purple-on-white defaults.
- No heavy shadows or glow effects.
- Avoid dense, tiny typography.

## Recommendation
Go with **Paper Ops** to balance clarity, warmth, and long-session comfort.

## Phase 2 Preview (Implementation)
- Centralize QSS tokens.
- Bundle Plex fonts + register in app.
- Apply to sidebar, roadmap, agents, chat.
- Add a subtle paper texture / gradient background.
