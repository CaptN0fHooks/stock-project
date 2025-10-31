import axios from "axios";

async function loadSummary() {
  const res = await axios.get("http://localhost:8000/api/summary");
  const data = res.data;

  const root = document.getElementById("app");
  root.innerHTML = `
    <h1 style="font-family:sans-serif;">Market Summary</h1>
    <p><strong>As of:</strong> ${data.as_of}</p>
    <ul>
      ${data.indices
        .map(i => `<li>${i.symbol}: ${i.price} (${i.pct.toFixed(2)}%)</li>`)
        .join("")}
    </ul>
  `;
}

loadSummary();
