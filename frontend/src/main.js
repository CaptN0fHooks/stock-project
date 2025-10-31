const API = "http://localhost:8000/api/summary?live=1";

const elStatus = document.getElementById("status");
const elCards  = document.getElementById("cards");
const elRaw    = document.getElementById("raw");

function card(title, bodyHtml) {
  const div = document.createElement("div");
  div.className = "card";
  div.innerHTML = `<div class="k">${title}</div><div>${bodyHtml}</div>`;
  return div;
}

async function run() {
  try {
    const t0 = performance.now();
    const res = await fetch(API);
    const t1 = performance.now();
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const ms = Math.round(t1 - t0);
    elStatus.innerHTML = `<span class="ok">Backend OK</span> (${ms} ms) — as_of: <code>${data.as_of}</code>`;

    // Sources
    elCards.appendChild(card("Sources", `<pre>${JSON.stringify(data.sources, null, 2)}</pre>`));

    // Indices (show first 3 if present)
    if (Array.isArray(data.indices)) {
      const rows = data.indices.slice(0,3).map(q => 
        `<div><b>${q.symbol || "(?)"}</b> — price: ${q.price ?? 0} | pct: ${q.pct ?? 0}</div>`
      ).join("");
      elCards.appendChild(card("Indices (sample)", rows || "<i>none</i>"));
    }

    // Sectors (top 5)
    if (Array.isArray(data.sectors)) {
      const rows = data.sectors.slice(0,5).map(s => 
        `<div><b>${s.symbol}</b> ${s.name} — ${s.pct}%</div>`
      ).join("");
      elCards.appendChild(card("Sectors (top 5)", rows || "<i>none</i>"));
    }

    // Posture
    if (data.session_posture) {
      elCards.appendChild(card(
        "Session Posture",
        `<div><b>${data.session_posture.label}</b> — score: ${data.session_posture.score}</div>
         <pre>${JSON.stringify(data.session_posture.components, null, 2)}</pre>`
      ));
    }

    // Raw
    elRaw.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    elStatus.innerHTML = `<span class="bad">Backend ERROR:</span> <code>${String(err)}</code>`;
  }
}

run();
