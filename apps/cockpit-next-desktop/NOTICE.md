# NOTICE

Cockpit Next reuses and adapts parts of the Pixel Agents project:

- Project: https://github.com/pablodelucca/pixel-agents
- License: MIT
- Reused code: `webview-ui/src/office/*` rendering/layout engine and related support modules.

Adaptation performed in this repository:

- VS Code message bridge removed in favor of Cockpit REST + WebSocket + Tauri invoke.
- Pixel Home integrated as default Cockpit landing page.
- Agent lifecycle tied to terminal lifecycle through Cockpit backend contracts.

Only open assets are embedded by default.
