const timelineData = [
  { label: "Wave14", value: 100, color: "#0d5f78" },
  { label: "Wave15", value: 100, color: "#1e7f54" },
  { label: "Wave16", value: 82, color: "#d26b2f" },
  { label: "Wave17 prep", value: 24, color: "#7e8c95" },
];

const deltaData = [
  { label: "Dispatch clarity", before: 38, now: 86 },
  { label: "False stale rate", before: 72, now: 21 },
  { label: "Operator launch clarity", before: 40, now: 90 },
  { label: "Cross-root confidence", before: 45, now: 83 },
];

function createBarRow(label, value, color) {
  const row = document.createElement("div");
  row.className = "bar-row";

  const labelEl = document.createElement("span");
  labelEl.className = "bar-label";
  labelEl.textContent = label;

  const track = document.createElement("div");
  track.className = "bar-track";

  const fill = document.createElement("div");
  fill.className = "bar-fill";
  fill.style.background = color;
  fill.dataset.width = String(value);

  track.appendChild(fill);

  const val = document.createElement("span");
  val.className = "bar-val";
  val.textContent = `${value}%`;

  row.appendChild(labelEl);
  row.appendChild(track);
  row.appendChild(val);
  return row;
}

function renderTimelineChart() {
  const target = document.getElementById("timeline-chart");
  if (!target) return;
  timelineData.forEach((entry) => {
    target.appendChild(createBarRow(entry.label, entry.value, entry.color));
  });
}

function renderDeltaChart() {
  const target = document.getElementById("delta-chart");
  if (!target) return;

  deltaData.forEach((entry) => {
    const rowBefore = createBarRow(`${entry.label} (before)`, entry.before, "#a8b4bc");
    const rowNow = createBarRow(`${entry.label} (now)`, entry.now, "#0d5f78");
    target.appendChild(rowBefore);
    target.appendChild(rowNow);
  });
}

function animateBars() {
  const fills = document.querySelectorAll(".bar-fill");
  fills.forEach((el) => {
    const width = Number(el.dataset.width || "0");
    requestAnimationFrame(() => {
      el.style.width = `${width}%`;
    });
  });
}

function setupScrollReveal() {
  const blocks = document.querySelectorAll(".section, .diagram-block, .chart-card, .info-card, .addon-card");
  blocks.forEach((el) => el.classList.add("reveal"));

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 }
  );

  blocks.forEach((el) => observer.observe(el));
}

function setupActiveNav() {
  const links = Array.from(document.querySelectorAll(".main-nav a"));
  const byId = new Map();
  links.forEach((link) => {
    const id = link.getAttribute("href")?.replace("#", "");
    if (id) byId.set(id, link);
  });

  const sections = Array.from(document.querySelectorAll("main section[id]"));
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        links.forEach((l) => l.classList.remove("is-active"));
        const link = byId.get(entry.target.id);
        if (link) link.classList.add("is-active");
      });
    },
    { rootMargin: "-40% 0px -50% 0px", threshold: 0.1 }
  );

  sections.forEach((sec) => observer.observe(sec));
}

window.addEventListener("DOMContentLoaded", () => {
  renderTimelineChart();
  renderDeltaChart();
  animateBars();
  setupScrollReveal();
  setupActiveNav();
});
