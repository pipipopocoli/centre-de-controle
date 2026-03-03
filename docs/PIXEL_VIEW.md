# Pixel View (Wave21)

## Goal

Render a git-pixel style heatmap of project activity in Cockpit Desktop.

## Data source

- Chat activity: `chat/global.ndjson`
- Run activity: `runs/*.json`
- Agent state updates: `agents/*/state.json`

## API

- Endpoint: `GET /v1/projects/{id}/pixel-feed?window=24h|7d|30d`
- Response includes:
  - `window`
  - `bucket_minutes`
  - `generated_at_utc`
  - `rows[]` by agent with `cells[]` intensity metrics

## Desktop behavior

- `Pixel View` tab refreshes every ~7s.
- Window selector:
  - `24h`
  - `7d`
  - `30d`
- Cell tooltip shows bucket timestamp + chat/runs/state counts.

## Event integration

- Websocket event `pixel.updated` is emitted after agentic and voice operations.

