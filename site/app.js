// --- EMBEDDED DATA (OFFLINE-FIRST) ---
const ROADMAP_DATA = [
  {
    "id": "p0",
    "name": "Phase 0: Le Grand Merge (Socle)",
    "status": "done",
    "start": 0,
    "duration": 2,
    "color": "#2da44e",
    "details": [
      { "task": "F1: Atomic Write (L'Airbag)", "dod": "Zero data loss on crash", "test": "repro_atomic_write.py" },
      { "task": "F2: 12-Item Cap (Le Limiteur)", "dod": "Hard truncation > 12 items", "test": "test_task_cap.py" },
      { "task": "F3: Gatekeeper (Le Videur)", "dod": "Blocks run if no project_id", "test": "test_gatekeeper.py" },
      { "task": "F4: Bible Parser (Le Radar)", "dod": "UI shows Risks/Skills from docs", "test": "test_bible_parsing.py" }
    ]
  },
  {
    "id": "p1",
    "name": "Phase 1: Orchestration",
    "status": "active",
    "start": 2,
    "duration": 3,
    "color": "#0969da",
    "details": [
      { "task": "Agent Registry JSON", "dod": "Single source of truth", "test": "verify_registry_load.py" },
      { "task": "SOUL.md Loading", "dod": "Personality injection successful", "test": "test_soul_loader.py" },
      { "task": "Skills Versioning", "dod": "Hash comparison on load", "test": "test_skill_integrity.py" }
    ]
  },
  {
    "id": "p2",
    "name": "Phase 2: Dispatch Durable",
    "status": "pending",
    "start": 5,
    "duration": 4,
    "color": "#8250df",
    "details": [
      { "task": "Persistent Task Queue", "dod": "SQLite backed queue", "test": "test_queue_persistence.py" },
      { "task": "Task Manager UI", "dod": "Real-time 'Airport' view", "test": "visual_qc_dashboard.py" },
      { "task": "Event Log", "dod": "Structured immutable log", "test": "test_event_logger.py" }
    ]
  },
  {
    "id": "p3",
    "name": "Phase 3: Mémoire Prog.",
    "status": "pending",
    "start": 9,
    "duration": 5,
    "color": "#bf3989",
    "details": [
      { "task": "FTS5 Implementation", "dod": "Keyword search < 50ms", "test": "benchmark_search.py" },
      { "task": "Context Packer", "dod": "Smart trim > 4k tokens", "test": "test_context_packer.py" },
      { "task": "Vector Fallback", "dod": "ChromaDB setup if needed", "test": "integration_test_vector.py" }
    ]
  },
  {
    "id": "p4",
    "name": "Phase 4: Platform Router",
    "status": "pending",
    "start": 14,
    "duration": 6,
    "color": "#bc8cff",
    "details": [
      { "task": "Multi-Runtime Switch", "dod": "Codex <-> Antigravity <-> Ollama", "test": "test_provider_switch.py" },
      { "task": "Circuit Breaker", "dod": "Stop calls after 3 fails", "test": "test_circuit_breaker.py" },
      { "task": "Budget Enforcement", "dod": "Hard limit tokens/day", "test": "test_budget_limits.py" }
    ]
  },
  {
    "id": "p5",
    "name": "Phase 5: Sécurité",
    "status": "pending",
    "start": 20,
    "duration": 4,
    "color": "#cf222e",
    "details": [
      { "task": "Capability System", "dod": "Granular permissions enforced", "test": "test_permission_denial.py" },
      { "task": "Sandbox Profiles", "dod": "Docker/WASM isolation", "test": "test_sandbox_escape.py" },
      { "task": "Secrets Redaction", "dod": "No plaintext API keys in logs", "test": "scan_logs_for_secrets.py" }
    ]
  },
  {
    "id": "p6",
    "name": "Phase 6: Puissance",
    "status": "pending",
    "start": 24,
    "duration": 8,
    "color": "#1f883d",
    "details": [
      { "task": "Local Vector Store", "dod": "Full semantic search", "test": "measure_recall.py" },
      { "task": "Ollama Integration", "dod": "100% Local LLM support", "test": "test_ollama_ping.py" },
      { "task": "Eval Harness", "dod": "Auto-regression check", "test": "run_full_suite.py" }
    ]
  }
];

const SKILLS_DATA = {
  "taxonomy": [
    { "id": "t1", "name": "Read-only Intelligence", "perms": "fs:read", "icon": "👀", "desc": "Mapping, Search, Logs. Risk: Low." },
    { "id": "t2", "name": "Safe Write", "perms": "fs:write (workspace)", "icon": "✍️", "desc": "Docs, Tests, Refactor. Risk: Medium." },
    { "id": "t3", "name": "Shell Restricted", "perms": "shell (allowlist)", "icon": "🐚", "desc": "Linter, Tests, Git. Risk: High." },
    { "id": "t4", "name": "Networked", "perms": "net:egress (whitelist)", "icon": "🌐", "desc": "Fetch docs, API calls. Risk: High." },
    { "id": "t5", "name": "Secrets-aware", "perms": "env:secrets", "icon": "🔑", "desc": "Deploy, Publish. Risk: Critical." }
  ],
  "mvp_skills": [
    { "name": "Repo Navigator", "type": "t1", "trust": "Tier 0" },
    { "name": "Search FTS", "type": "t1", "trust": "Tier 0" },
    { "name": "Patch Builder", "type": "t2", "trust": "Tier 0" },
    { "name": "Test Runner", "type": "t3", "trust": "Tier 1" },
    { "name": "Lint/Format", "type": "t3", "trust": "Tier 1" },
    { "name": "Doc Writer", "type": "t2", "trust": "Tier 1" }
  ]
};

const RUN_DATA = [
  { "time": "00:00", "agent": "Clems", "action": "PLAN", "msg": "Analyzing request: 'Fix broken login button'. Reading auth.py...", "tokens": 120 },
  { "time": "00:02", "agent": "Clems", "action": "TOOL", "msg": "search_code('login button', 'app/ui/login.py')", "tokens": 45 },
  { "time": "00:05", "agent": "System", "action": "OUTPUT", "msg": "Found 3 matches in app/ui/login.py:42", "tokens": 300 },
  { "time": "00:08", "agent": "Clems", "action": "DELEGATE", "msg": "Assigning task to Victor (Backend): 'Patch auth validation logic'.", "tokens": 80 },
  { "time": "00:10", "agent": "Victor", "action": "THINK", "msg": "Loading skill 'py-expert'. Checking capability 'fs:write'. Allowed.", "tokens": 150 },
  { "time": "00:15", "agent": "Victor", "action": "TOOL", "msg": "patch_file('app/auth/validator.py', diff=...)", "tokens": 600 },
  { "time": "00:18", "agent": "Gatekeeper", "action": "AUDIT", "msg": "Reviewing diff... Atomic write engaged. Backup created.", "tokens": 0 },
  { "time": "00:20", "agent": "System", "action": "SUCCESS", "msg": "File updated. Running tests...", "tokens": 50 },
  { "time": "00:25", "agent": "Victor", "action": "TOOL", "msg": "run_test('tests/test_auth.py')", "tokens": 60 },
  { "time": "00:30", "agent": "System", "action": "PASS", "msg": "Tests passed: 4/4. Time: 0.4s.", "tokens": 0 },
  { "time": "00:32", "agent": "Clems", "action": "DONE", "msg": "Mission accomplished. Adding entry to Memory.", "tokens": 100 }
];

// --- APP LOGIC ---

document.addEventListener('DOMContentLoaded', () => {
  // Direct rendering, no fetch needed
  renderGantt(ROADMAP_DATA);
  renderSkills(SKILLS_DATA);
  setupSimulation(RUN_DATA);
  renderArchitecture();
  renderMemoryPipeline();
});

// --- SIMULATION ENGINE ---
let simRunData = [];
function setupSimulation(data) {
  simRunData = data;
  const btn = document.getElementById('btn-sim-run');
  if (btn) btn.onclick = startSimulation;

  // Also bind hero button
  const heroBtn = document.getElementById('btn-hero-sim');
  if (heroBtn) heroBtn.onclick = () => {
    document.getElementById('simulation').scrollIntoView({ behavior: 'smooth' });
    setTimeout(startSimulation, 800);
  };
}

function startSimulation() {
  const consoleDiv = document.getElementById('sim-console-output');
  consoleDiv.innerHTML = ''; // clear
  let delay = 0;

  simRunData.forEach((event, i) => {
    const stepDelay = event.action === 'THINK' ? 800 : event.action === 'TOOL' ? 1200 : 400;
    delay += stepDelay;

    setTimeout(() => {
      const row = document.createElement('div');
      row.className = `sim-entry ${event.action}`;
      row.innerHTML = `
                <span class="sim-time">[${event.time}]</span>
                <span class="sim-agent">${event.agent}</span>
                <span style="color:#8b949e">[${event.action}]</span> 
                ${event.msg} 
                ${event.tokens > 0 ? `<span style="float:right; opacity:0.5; font-size:0.8em">${event.tokens}t</span>` : ''}
            `;
      consoleDiv.appendChild(row);
      consoleDiv.scrollTop = consoleDiv.scrollHeight;
      if (event.tokens > 0) updateMockMetrics(event.tokens);
    }, delay);
  });
}

function updateMockMetrics(tokens) {
  const el = document.getElementById('live-token-count');
  if (el) {
    let current = parseInt(el.innerText.replace(/,/g, '')) || 0;
    el.innerText = (current + tokens).toLocaleString();
  }
}

// --- SKILLS RENDERER ---
function renderSkills(data) {
  const taxonomyContainer = document.getElementById('skills-taxonomy');
  if (taxonomyContainer) {
    taxonomyContainer.innerHTML = data.taxonomy.map(t => `
            <div class="card" style="text-align:center">
                <div class="card-icon">${t.icon}</div>
                <h4>${t.name}</h4>
                <div class="mono" style="font-size:0.75em; margin-bottom:0.5rem">${t.perms}</div>
                <p style="font-size:0.9em">${t.desc}</p>
            </div>
        `).join('');
  }

  const mvpContainer = document.getElementById('skills-mvp');
  if (mvpContainer) {
    let html = '<ul style="list-style:none; padding:0;">';
    data.mvp_skills.forEach(s => {
      const badgeClass = s.trust === 'Tier 0' ? 'badge-tier0' : 'badge-tier1';
      html += `<li style="margin-bottom:0.5rem; display:flex; justify-content:space-between; border-bottom:1px solid #eee; padding-bottom:4px;">
                <span>${s.name}</span>
                <span class="badge ${badgeClass}" style="font-size:0.65em">${s.trust}</span>
            </li>`;
    });
    html += '</ul>';
    mvpContainer.innerHTML = html;
  }
}

// --- GANTT RENDERER ---
function renderGantt(roadmap) {
  const container = document.querySelector('.gantt-chart');
  if (!container) return;

  const svgNS = "http://www.w3.org/2000/svg";
  const width = container.clientWidth || 900;
  const height = roadmap.length * 60 + 50;

  const svg = document.createElementNS(svgNS, "svg");
  svg.setAttribute("width", "100%");
  svg.setAttribute("height", height);
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

  const totalDuration = 32;
  const pxPerWeek = (width - 250) / totalDuration;

  roadmap.forEach((phase, index) => {
    const y = index * 60 + 40;
    const barX = 220 + (phase.start * pxPerWeek);
    const barW = Math.max(phase.duration * pxPerWeek, 10);

    const labelG = document.createElementNS(svgNS, "g");
    const text = document.createElementNS(svgNS, "text");
    text.setAttribute("x", 10);
    text.setAttribute("y", y + 20);
    text.setAttribute("font-weight", "bold");
    text.setAttribute("fill", "#24292f");
    text.textContent = phase.name;
    labelG.appendChild(text);
    svg.appendChild(labelG);

    const bar = document.createElementNS(svgNS, "rect");
    bar.setAttribute("x", barX);
    bar.setAttribute("y", y);
    bar.setAttribute("width", barW);
    bar.setAttribute("height", 30);
    bar.setAttribute("rx", 6);
    bar.setAttribute("fill", phase.color);
    bar.setAttribute("cursor", "pointer");
    bar.setAttribute("opacity", "0.9");

    bar.onmouseover = () => bar.setAttribute("opacity", "1");
    bar.onmouseout = () => bar.setAttribute("opacity", "0.9");
    bar.onclick = () => showPhaseDetails(phase);

    svg.appendChild(bar);

    const dot = document.createElementNS(svgNS, "circle");
    dot.setAttribute("cx", 200);
    dot.setAttribute("cy", y + 15);
    dot.setAttribute("r", 4);
    dot.setAttribute("fill", phase.status === 'done' ? '#2da44e' : phase.status === 'active' ? '#0969da' : '#d0d7de');
    svg.appendChild(dot);
  });

  container.innerHTML = '';
  container.appendChild(svg);
}

function showPhaseDetails(phase) {
  const details = document.querySelector('.gantt-details');
  if (details) {
    details.innerHTML = `
            <span class="badge" style="background:${phase.color}; color:white;">${phase.id.toUpperCase()}</span>
            <h3 style="margin-top:0">${phase.name}</h3>
            <p><strong>Status:</strong> ${phase.status.toUpperCase()}</p>
            <h4>Deliverables & DoD</h4>
            <ul>
                ${phase.details.map(d => `<li>
                    <strong>${d.task}</strong>: ${d.dod}
                    <br><code class="mono" style="font-size:0.75em">${d.test}</code>
                </li>`).join('')}
            </ul>
        `;
    details.classList.add('active');
    details.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

// --- ARCHITECTURE SVG ---
function renderArchitecture() {
  const el = document.getElementById('arch-svg');
  if (!el) return;
  el.innerHTML = `<svg viewBox="0 0 800 350" xmlns="http://www.w3.org/2000/svg">
        <style>.layer { fill: #f6f8fa; stroke: #d0d7de; rx: 8; } .txt { font-family: sans-serif; font-size: 12px; font-weight: 600; text-anchor: middle; fill: #57606a; } .box { stroke-width: 2px; rx: 4; fill: white; cursor: pointer; } .box:hover { fill: #eef; }</style>
        <rect x="50" y="30" width="700" height="80" class="layer" /> <text x="400" y="25" class="txt">INTERFACE (UI)</text>
        <rect x="50" y="130" width="700" height="90" class="layer" /> <text x="400" y="125" class="txt">SERVICE LAYER (LOGIC)</text>
        <rect x="50" y="240" width="700" height="80" class="layer" /> <text x="400" y="235" class="txt">DATA LAYER (STATE)</text>
        
        <rect x="100" y="45" width="120" height="50" class="box" stroke="#0969da" /><text x="160" y="75" class="txt" style="fill:#0969da">Qt Desktop</text>
        <rect x="580" y="45" width="120" height="50" class="box" stroke="#0969da" /><text x="640" y="75" class="txt" style="fill:#0969da">CLI / TUI</text>
        
        <rect x="340" y="150" width="120" height="50" class="box" stroke="#8250df" /><text x="400" y="180" class="txt" style="fill:#8250df">Platform Router</text>
        <rect x="150" y="150" width="100" height="50" class="box" stroke="#cf222e" /><text x="200" y="180" class="txt" style="fill:#cf222e">Gatekeeper</text>
        <rect x="550" y="150" width="100" height="50" class="box" stroke="#bf3989" /><text x="600" y="180" class="txt" style="fill:#bf3989">Memory Eng.</text>
        
        <rect x="250" y="255" width="140" height="50" class="box" stroke="#2da44e" /><text x="320" y="285" class="txt" style="fill:#2da44e">BrainFS (JSON)</text>
        <rect x="410" y="255" width="140" height="50" class="box" stroke="#2da44e" /><text x="480" y="285" class="txt" style="fill:#2da44e">Vector Store</text>

        <g stroke="#8b949e" stroke-width="2" marker-end="url(#arr)">
            <line x1="160" y1="95" x2="200" y2="150" />
            <line x1="640" y1="95" x2="600" y2="150" />
            <line x1="400" y1="200" x2="400" y2="240" />
            <line x1="200" y1="200" x2="280" y2="255" />
        </g>
        <defs><marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#8b949e" /></marker></defs>
    </svg>`;
}

function renderMemoryPipeline() {
  // Basic placeholder for now, focused on skills/simulation
}
