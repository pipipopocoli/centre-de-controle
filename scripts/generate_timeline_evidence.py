import sys
import os
from pathlib import Path

# Output directory
OUTPUT_DIR = Path("docs/reports/cp01-ui-qa/evidence")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_timeline_evidence():
    scenarios = [
        {
            "id": "TL-01",
            "desc": "Hybrid Timeline - Normal",
            "milestones": [
                {"label": "Wave 1 - Foundation", "status": "done", "desc": "Project setup complete"},
                {"label": "Wave 2 - Core", "status": "done", "desc": "Agents online"},
                {"label": "Wave 3 - Pilotage", "status": "active", "desc": "UI & Metrics (Current)", "id": "CP-0014"},
                {"label": "Wave 4 - cleanup", "status": "todo", "desc": "Refactor & Polish"},
                {"label": "Wave 5 - Launch", "status": "todo", "desc": "Public release"}
            ],
            "events": [
                {"time": "10:05", "lane": "runtime", "sev": "info", "title": "agent-1 task complete", "details": "Index updated"},
                {"time": "10:02", "lane": "delivery", "sev": "info", "title": "CP-0014 updated", "details": "Status: In Progress"},
                {"time": "09:55", "lane": "risk", "sev": "warn", "title": "high latency warn", "details": "Dispatch > 2s"},
                {"time": "09:45", "lane": "runtime", "sev": "info", "title": "system startup", "details": "All agents ready"}
            ]
        },
        {
            "id": "TL-02",
            "desc": "Hybrid Timeline - Degraded",
            "milestones": [
                 {"label": "Wave 1 - Foundation", "status": "done", "desc": "Project setup complete"},
                 {"label": "Wave 2 - Core", "status": "active", "desc": "Stalled on dependency", "id": "CP-0010"},
                 {"label": "Wave 3 - Pilotage", "status": "todo", "desc": "Blocked by Wave 2"},
                 {"label": "Wave 4 - cleanup", "status": "todo", "desc": "Pending"}
            ],
             "events": [
                {"time": "10:15", "lane": "runtime", "sev": "critical", "title": "connection reset", "details": "Backend unreachable"},
                {"time": "10:14", "lane": "risk", "sev": "critical", "title": "SLO violation", "details": "Success rate < 90%"},
                {"time": "10:12", "lane": "delivery", "sev": "warn", "title": "CP-0010 blocked", "details": "Missing assets"},
                {"time": "10:00", "lane": "runtime", "sev": "info", "title": "retry attempt 3", "details": "Backoff 30s"}
            ]
        }
    ]

    for scen in scenarios:
        # Generate SVG for Milestone Route
        svg_circles = ""
        y_pos = 40
        for m in scen["milestones"]:
            color = "#C4C4C4" # todo
            if m["status"] == "done": color = "#22C55E"
            elif m["status"] == "active": color = "#2C5DFF"
            
            svg_circles += f'<circle cx="30" cy="{y_pos}" r="8" fill="{color}" />'
            svg_circles += f'<text x="50" y="{y_pos+5}" font-family="Inter, sans-serif" font-size="13" font-weight="600" fill="#1C1C1C">{m["label"]}</text>'
            svg_circles += f'<text x="50" y="{y_pos+20}" font-family="Inter, sans-serif" font-size="11" fill="#5E6167">{m["desc"]}</text>'
            if "id" in m:
                svg_circles += f'<text x="50" y="{y_pos-10}" font-family="Menlo, monospace" font-size="9" fill="#5E6167">{m["id"]}</text>'
            
            y_pos += 60

        route_height = y_pos
        route_svg = f'''
        <svg width="400" height="{route_height}" viewBox="0 0 400 {route_height}" xmlns="http://www.w3.org/2000/svg">
            <line x1="30" y1="30" x2="30" y2="{y_pos-60}" stroke="#1C1C1C" stroke-width="3" />
            {svg_circles}
        </svg>
        '''

        # Generate HTML Table for Events
        rows = ""
        for e in scen["events"]:
            color = "#1C1C1C"
            if e["sev"] == "warn": color = "#92400E"
            elif e["sev"] == "critical": color = "#B91C1C"
            
            rows += f'''
            <tr style="border-bottom: 1px solid #E5E7EB;">
                <td style="padding: 8px; font-family: monospace; font-size: 11px; color: #5E6167;">{e["time"]}</td>
                <td style="padding: 8px; font-size: 11px;">{e["lane"]}</td>
                <td style="padding: 8px; font-size: 11px; color: {color}; font-weight: 600;">{e["sev"]}</td>
                <td style="padding: 8px; font-size: 11px; color: {color};">{e["title"]} <span style="color: #9CA3AF;">| {e["details"]}</span></td>
            </tr>
            '''
        
        events_html = f'''
        <table style="width: 100%; border-collapse: collapse; text-align: left;">
            <thead style="background: #F3F4F6;">
                <tr>
                    <th style="padding: 8px; font-size: 11px; color: #374151;">Time</th>
                    <th style="padding: 8px; font-size: 11px; color: #374151;">Lane</th>
                    <th style="padding: 8px; font-size: 11px; color: #374151;">Sev</th>
                    <th style="padding: 8px; font-size: 11px; color: #374151;">Event</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        '''

        # Full Page
        full_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, system-ui, sans-serif; background: #F6F3EE; margin: 0; padding: 20px; }}
                .card {{ background: white; border-radius: 8px; border: 1px solid #D9D3C8; overflow: hidden; margin-bottom: 20px; }}
                .header {{ padding: 12px 16px; border-bottom: 1px solid #E5E7EB; }}
                .title {{ font-size: 15px; font-weight: 700; margin: 0; }}
                .subtitle {{ font-size: 12px; color: #6B7280; margin: 4px 0 0; }}
            </style>
        </head>
        <body>
            <h1>{scen["desc"]} (Evidence)</h1>
            <div class="card" style="width: 450px;">
                <div class="header">
                    <h2 class="title">Route du projet</h2>
                    <p class="subtitle">Evidence Capture Mode</p>
                </div>
                <div style="padding: 20px;">
                    {route_svg}
                </div>
                <div style="border-top: 1px solid #D9D3C8;">
                    {events_html}
                </div>
            </div>
        </body>
        </html>
        '''

        outfile = OUTPUT_DIR / f"scenario_{scen['id']}.html"
        outfile.write_text(full_html)
        print(f"Generated {outfile}")

if __name__ == "__main__":
    generate_timeline_evidence()
