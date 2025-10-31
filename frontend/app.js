const API = "http://localhost:8000";

async function getSummary() {
  const res = await fetch(`${API}/api/summary`);
  if (!res.ok) throw new Error("summary failed");
  return res.json();
}

function fmtPct(x){ return (x>=0?"+":"") + x.toFixed(2) + "%"; }
function clsPct(x){ return x>=0 ? "green" : "red"; }

function renderIndices(indices, vix){
  const iDiv = document.getElementById("indices");
  iDiv.innerHTML = indices.map(q => `
    <span class="chip ${clsPct(q.pct)}">${q.symbol}: ${q.price} (${fmtPct(q.pct)})</span>
  `).join("");
  const vixDiv = document.getElementById("vix");
  vixDiv.innerHTML = `<span class="chip ${clsPct(-vix.pct)}">VIX: ${vix.price} (${fmtPct(vix.pct)})</span>`;
}

function renderSectors(sectors){
  const strip = document.getElementById("sector-strip");
  strip.className = "strip";
  strip.innerHTML = sectors.map(s => `
    <div class="cell ${clsPct(s.pct)}">${s.symbol} ${fmtPct(s.pct)}</div>
  `).join("");
}

function renderPosture(sp){
  document.getElementById("posture-score").textContent = `${sp.label} (${sp.score})`;
  document.getElementById("posture-notes").innerHTML = sp.notes.map(n => `<li class="muted">${n}</li>`).join("");
}

async function refresh(){
  try {
    const sum = await getSummary();
    document.getElementById("asof").textContent = `As of: ${sum.as_of}`;
    renderIndices(sum.indices, sum.vix);
    renderSectors(sum.sectors);
    renderPosture(sum.session_posture);
  } catch(e){
    console.error(e);
  }
}

// ---------- Watchlist ----------
async function getWL(){ const r = await fetch(`${API}/api/watchlist`); return r.json(); }
async function addWL(items){ 
  const r = await fetch(`${API}/api/watchlist`, {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(items)});
  return r.json();
}
async function delWL(sym){ 
  const r = await fetch(`${API}/api/watchlist/${encodeURIComponent(sym)}`, {method:"DELETE"});
  return r.json();
}
async function getMini(symbols){ 
  const r = await fetch(`${API}/api/miniquotes?symbols=${symbols.join(",")}`); 
  return r.json(); 
}

function sparkPath(values, w=120, h=28){
  if(!values || values.length === 0) return "";
  const min = Math.min(...values), max = Math.max(...values);
  const range = (max - min) || 1;
  const step = w / (values.length - 1);
  return values.map((v,i)=>{
    const x = i*step;
    const y = h - ((v-min)/range)*h;
    return (i===0 ? "M" : "L") + x.toFixed(2) + " " + y.toFixed(2);
  }).join(" ");
}

async function renderWL(){
  const wl = await getWL();
  const symbols = wl.symbols.map(s => s.symbol);
  const container = document.getElementById("wl-items");
  container.innerHTML = "";
  if(symbols.length === 0){ container.innerHTML = '<div class="muted">No symbols yet.</div>'; return; }
  const minis = await getMini(symbols);
  minis.forEach(m => {
    const row = document.createElement("div");
    row.className = "row";
    const path = sparkPath(m.sparkline);
    row.innerHTML = `
      <div>${m.symbol}</div>
      <div class="${clsPct(m.pct)}">${fmtPct(m.pct)}</div>
      <svg class="spark" viewBox="0 0 120 28"><path d="${path}" fill="none" stroke="currentColor" stroke-width="1"/></svg>
      <button data-sym="${m.symbol}">Remove</button>
    `;
    row.querySelector("button").addEventListener("click", async (e)=>{
      await delWL(e.target.dataset.sym); renderWL();
    });
    container.appendChild(row);
  });
}

document.getElementById("wl-form").addEventListener("submit", async (e)=>{
  e.preventDefault();
  const sym = document.getElementById("wl-symbol").value.trim().toUpperCase();
  const notes = document.getElementById("wl-notes").value.trim();
  if(!sym) return;
  await addWL([{symbol: sym, notes}]);
  document.getElementById("wl-symbol").value = "";
  document.getElementById("wl-notes").value = "";
  renderWL();
});

refresh();
renderWL();
setInterval(refresh, 60000);
