# Reference - Vercel "React Best Practices" (2026-01-14)

Source:
- https://vercel.com/blog/introducing-react-best-practices

Why this matters to Cockpit:
- Cockpit UI is PySide6/QSS today (not React), so we do NOT apply these rules directly.
- But the underlying mindset is useful: fix the big problems first (waterfalls, payload size, slow data flows), then micro-opt.
- If we ever build a web UI (React/Next.js), this becomes directly actionable.

Key idea (the ordering):
1) Eliminate async waterfalls.
2) Reduce bundle size / ship less JS.
3) Then tune rendering, re-renders, and client-side fetching.

What we can borrow now (Qt/PySide6):
- Avoid "refresh everything" loops: only reload what changed, debounce timers, avoid disk re-reads every tick.
- Make performance work visible: measure before optimizing, prioritize the biggest bottleneck.

How to use later (web UI / React):
- Treat their checklist as "guardrails" for PR reviews.
- Consider a similar approach for Cockpit docs: concise rules + severity (critical/high/med/low) + examples.

