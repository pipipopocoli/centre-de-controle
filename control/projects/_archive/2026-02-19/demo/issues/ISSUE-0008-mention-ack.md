# ISSUE-0008 - Mention ack + state/journal update

- Owner: victor
- Phase: Implement
- Status: Done

## Objective
- Make @leo/@victor/@clems mentions visible and traceable.

## Scope (In)
- On mention, update agent state (status + heartbeat).
- Append a journal entry to agent journal.ndjson.
- Emit a system ack message in chat.

## Scope (Out)
- Notifications / OS-level popups.

## Done (Definition)
- Mention updates agent status to "pinged".
- Mention appends journal entry with event=mention.
- Ack message appears in chat feed.

## Links
- STATE.md: control/projects/demo/STATE.md
- DECISIONS.md: control/projects/demo/DECISIONS.md
- PR: https://github.com/pipipopocoli/centre-de-controle/pull/9
