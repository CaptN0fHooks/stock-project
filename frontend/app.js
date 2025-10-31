const statusEl = document.getElementById('status');
const indicesEl = document.getElementById('indices');
const vixEl = document.getElementById('vix');
const sectorsEl = document.getElementById('sectors');

// backend base
const BASE = (import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000').replace(/\/+$/,'');

async function fetchJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

(async () => {
  try {
    statusEl.textContent = 'Fetching /api/summary…';
    const data = await fetchJSON(`${BASE}/api/summary?live=1`);

    statusEl.textContent = `OK • as_of ${data.as_of} • sources: indices=${data.sources.indices}, vix=${data.sources.vix}`;

    indicesEl.textContent = JSON.stringify(data.indices, null, 2);
    vixEl.textContent = JSON.stringify(data.vix, null, 2);
    sectorsEl.textContent = JSON.stringify(data.sectors, null, 2);
  } catch (err) {
    statusEl.textContent = 'Error: ' + err.message;
  }
})();
