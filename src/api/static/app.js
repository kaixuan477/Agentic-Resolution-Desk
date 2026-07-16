// Approval Console — vanilla JS, no build step.
// Talks to the same FastAPI service that powers the agents.

const queueEl = document.getElementById("queue");
const emptyEl = document.getElementById("empty");
const statusEl = document.getElementById("status");
const template = document.getElementById("card-template");

function setStatus(text) {
  statusEl.textContent = text;
}

function formatAmount(value) {
  if (value === null || value === undefined) return "—";
  return `$${Number(value).toFixed(2)}`;
}

function renderCard(item) {
  const node = template.content.firstElementChild.cloneNode(true);
  node.querySelector(".tool").textContent = item.proposed_tool || "action";
  node.querySelector(".thread").textContent = item.thread_id;
  node.querySelector(".user").textContent = item.proposed_user_id || "—";
  node.querySelector(".amount").textContent = formatAmount(item.proposed_amount);
  node.querySelector(".message").textContent =
    item.messages && item.messages.length ? item.messages[item.messages.length - 1] : "";

  const approveBtn = node.querySelector(".approve");
  const denyBtn = node.querySelector(".deny");
  approveBtn.addEventListener("click", () => decide(item.thread_id, "approved", node));
  denyBtn.addEventListener("click", () => decide(item.thread_id, "denied", node));
  return node;
}

async function decide(threadId, decision, cardNode) {
  cardNode.querySelectorAll("button").forEach((b) => (b.disabled = true));
  setStatus(`Submitting ${decision} for ${threadId}…`);
  try {
    const res = await fetch("/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ thread_id: threadId, decision }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    setStatus(`${threadId} ${decision}.`);
    await load();
  } catch (err) {
    setStatus(`Failed: ${err.message}`);
    cardNode.querySelectorAll("button").forEach((b) => (b.disabled = false));
  }
}

async function load() {
  setStatus("Loading…");
  try {
    const res = await fetch("/pending/details");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const items = await res.json();
    queueEl.replaceChildren(...items.map(renderCard));
    emptyEl.hidden = items.length > 0;
    setStatus(`${items.length} awaiting approval.`);
  } catch (err) {
    setStatus(`Failed to load: ${err.message}`);
  }
}

document.getElementById("refresh").addEventListener("click", load);
load();
setInterval(load, 10000);
