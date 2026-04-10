const API = "/api";
let sessionId = null;
let selectedPreset = null;
let currentTab = "presets";

// DOM refs
const presetsTab = document.getElementById("presets-tab");
const customTab = document.getElementById("custom-tab");
const launchBtn = document.getElementById("launch-btn");
const chatArea = document.getElementById("chat-area");
const emptyState = document.getElementById("empty-state");
const msgInput = document.getElementById("msg-input");
const sendBtn = document.getElementById("send-btn");
const agentTitle = document.getElementById("agent-title");
const sessionBadge = document.getElementById("session-badge");
const configEditor = document.getElementById("config-editor");

// --- Tabs ---
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    currentTab = tab.dataset.tab;
    presetsTab.style.display = currentTab === "presets" ? "" : "none";
    customTab.style.display = currentTab === "custom" ? "" : "none";
    updateLaunchBtn();
  });
});

// --- Load presets ---
async function loadPresets() {
  const res = await fetch(`${API}/presets`);
  const presets = await res.json();
  presetsTab.innerHTML = "";
  for (const [name, cfg] of Object.entries(presets)) {
    const card = document.createElement("div");
    card.className = "preset-card";
    card.innerHTML = `<h3>${cfg.name}</h3><p>${cfg.description}</p>`;
    card.addEventListener("click", () => {
      document.querySelectorAll(".preset-card").forEach((c) => c.classList.remove("active"));
      card.classList.add("active");
      selectedPreset = name;
      configEditor.value = JSON.stringify(cfg, null, 2);
      updateLaunchBtn();
    });
    presetsTab.appendChild(card);
  }
}

function updateLaunchBtn() {
  if (currentTab === "presets") {
    launchBtn.disabled = !selectedPreset;
  } else {
    launchBtn.disabled = !configEditor.value.trim();
  }
}

configEditor.addEventListener("input", updateLaunchBtn);

// --- Launch agent ---
launchBtn.addEventListener("click", async () => {
  launchBtn.disabled = true;
  launchBtn.textContent = "Launching...";

  let body;
  if (currentTab === "presets" && selectedPreset) {
    body = { preset: selectedPreset };
  } else {
    try {
      body = { config: JSON.parse(configEditor.value) };
    } catch {
      alert("Invalid JSON config");
      launchBtn.disabled = false;
      launchBtn.textContent = "Launch Agent";
      return;
    }
  }

  const res = await fetch(`${API}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json();
    alert(`Error: ${err.detail}`);
    launchBtn.disabled = false;
    launchBtn.textContent = "Launch Agent";
    return;
  }

  const data = await res.json();
  sessionId = data.session_id;

  agentTitle.textContent = data.agent_name;
  sessionBadge.textContent = `Session: ${sessionId}`;
  sessionBadge.style.display = "";
  emptyState.style.display = "none";
  chatArea.innerHTML = "";

  msgInput.disabled = false;
  sendBtn.disabled = false;
  msgInput.focus();

  launchBtn.textContent = "Launch Agent";
  launchBtn.disabled = false;
});

// --- Chat ---
async function sendMessage() {
  const text = msgInput.value.trim();
  if (!text || !sessionId) return;

  appendMessage("user", text);
  msgInput.value = "";
  msgInput.disabled = true;
  sendBtn.disabled = true;

  const thinkingEl = appendMessage("assistant", "Thinking...");
  thinkingEl.classList.add("loading");

  try {
    const res = await fetch(`${API}/sessions/${sessionId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    if (!res.ok) {
      const err = await res.json();
      thinkingEl.querySelector(".content").textContent = `Error: ${err.detail}`;
      thinkingEl.classList.remove("loading");
      return;
    }

    const data = await res.json();
    thinkingEl.querySelector(".content").textContent = data.response;
    thinkingEl.classList.remove("loading");
  } catch (e) {
    thinkingEl.querySelector(".content").textContent = `Network error: ${e.message}`;
    thinkingEl.classList.remove("loading");
  } finally {
    msgInput.disabled = false;
    sendBtn.disabled = false;
    msgInput.focus();
  }
}

sendBtn.addEventListener("click", sendMessage);
msgInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

function appendMessage(role, content) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.innerHTML = `<div class="role">${role}</div><div class="content">${escapeHtml(content)}</div>`;
  chatArea.appendChild(div);
  chatArea.scrollTop = chatArea.scrollHeight;
  return div;
}

function escapeHtml(text) {
  const d = document.createElement("div");
  d.textContent = text;
  return d.innerHTML;
}

// Init
loadPresets();
