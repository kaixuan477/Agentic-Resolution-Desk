// Audit trail view — read-only, consumes GET /audit.

const rowsEl = document.getElementById("rows");
const statusEl = document.getElementById("status");

function setStatus(text) {
  statusEl.textContent = text;
}

function cell(text) {
  const td = document.createElement("td");
  td.textContent = text;
  return td;
}

function renderRow(record) {
  const tr = document.createElement("tr");
  tr.appendChild(cell(record.timestamp));
  tr.appendChild(cell(record.tool));
  tr.appendChild(cell(record.user_id || "—"));
  tr.appendChild(cell(record.result_status));
  tr.appendChild(cell(JSON.stringify(record.arguments)));
  return tr;
}

async function load() {
  setStatus("Loading…");
  try {
    const res = await fetch("/audit?limit=200");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const records = await res.json();
    // Newest first.
    records.reverse();
    rowsEl.replaceChildren(...records.map(renderRow));
    setStatus(`${records.length} records.`);
  } catch (err) {
    setStatus(`Failed to load: ${err.message}`);
  }
}

document.getElementById("refresh").addEventListener("click", load);
load();
