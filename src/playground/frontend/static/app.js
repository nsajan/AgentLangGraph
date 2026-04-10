// ============================================================
// AgentLangGraph Playground — Pattern-Based Builder
// ============================================================

const API = "/api";
let currentPattern = "react";
let sessionId = null;
let workerCount = 2;

const configArea = document.getElementById("config-area");
const flowCanvas = document.getElementById("flow-canvas");
const flowBadge = document.getElementById("flow-badge");
const chatArea = document.getElementById("chat-area");
const emptyState = document.getElementById("empty-state");
const msgInput = document.getElementById("msg-input");
const sendBtn = document.getElementById("send-btn");
const chatTitle = document.getElementById("chat-title");
const sessionBadge = document.getElementById("session-badge");
const stepTrace = document.getElementById("step-trace");
const traceList = document.getElementById("trace-list");
const exportModal = document.getElementById("export-modal");
const exportContent = document.getElementById("export-content");
const modalTitle = document.getElementById("modal-title");

const PATTERN_COLORS = {
  react: "#6366f1", plan_execute: "#3b82f6",
  reflection: "#a855f7", supervisor: "#f59e0b",
};
const PATTERN_LABELS = {
  react: "ReAct", plan_execute: "Plan & Execute",
  reflection: "Reflection", supervisor: "Supervisor",
};
const MODELS = [
  { value: "claude-sonnet-4-20250514", label: "Claude Sonnet 4" },
  { value: "claude-haiku-4-5-20251001", label: "Claude Haiku 4.5" },
  { value: "claude-opus-4-20250514", label: "Claude Opus 4" },
];
const TOOLS = [
  { value: "calculator", label: "Calculator" },
  { value: "echo", label: "Echo" },
  { value: "current_time", label: "Current Time" },
];

// ============================================================
// PATTERN SELECTION
// ============================================================

document.querySelectorAll(".pattern-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".pattern-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentPattern = btn.dataset.pattern;
    renderConfigForm();
    renderFlowDiagram();
    flowBadge.textContent = PATTERN_LABELS[currentPattern];
    flowBadge.style.background = PATTERN_COLORS[currentPattern];
  });
});

// ============================================================
// CONFIG FORM RENDERING
// ============================================================

function modelSelect(id, selected) {
  const opts = MODELS.map(m =>
    `<option value="${m.value}" ${m.value === selected ? "selected" : ""}>${m.label}</option>`
  ).join("");
  return `<label class="form-label">Model<select class="form-select" id="${id}">${opts}</select></label>`;
}

function toolsCheckboxes(id, selected = []) {
  const checks = TOOLS.map(t =>
    `<label class="checkbox-row"><input type="checkbox" data-tool-group="${id}" value="${t.value}" ${selected.includes(t.value) ? "checked" : ""} /> ${t.label}</label>`
  ).join("");
  return `<label class="form-label">Tools<div class="tools-grid">${checks}</div></label>`;
}

function agentGroup(prefix, title, defaults = {}) {
  const color = PATTERN_COLORS[currentPattern];
  return `
    <div class="config-group">
      <div class="config-group-title"><span class="dot" style="background:${color}"></span>${title}</div>
      <div class="config-form">
        <label class="form-label">Name<input class="form-input" id="${prefix}-name" value="${defaults.name || prefix}" /></label>
        <label class="form-label">System Prompt<textarea class="form-textarea" id="${prefix}-prompt" rows="3">${defaults.prompt || "You are a helpful assistant."}</textarea></label>
        ${modelSelect(`${prefix}-model`, defaults.model || MODELS[0].value)}
        ${defaults.showTools !== false ? toolsCheckboxes(prefix, defaults.tools || []) : ""}
      </div>
    </div>`;
}

function renderConfigForm() {
  let html = `
    <label class="form-label">Agent Name<input class="form-input" id="agent-name" value="my-agent" /></label>
    <label class="form-label" style="margin-bottom:12px">Description<input class="form-input" id="agent-desc" value="" placeholder="What does this agent do?" /></label>`;

  if (currentPattern === "react") {
    html += agentGroup("agent", "Agent", {
      name: "agent",
      prompt: "You are a helpful assistant. Use tools when appropriate.",
      tools: ["calculator"],
    });
  } else if (currentPattern === "plan_execute") {
    html += agentGroup("planner", "Planner", {
      name: "planner",
      prompt: "You are a research planner. Break complex questions into clear, sequential steps.",
      showTools: false,
    });
    html += agentGroup("executor", "Executor", {
      name: "executor",
      prompt: "You are a research executor. Complete the assigned step thoroughly and concisely.",
      tools: ["calculator"],
    });
  } else if (currentPattern === "reflection") {
    html += agentGroup("generator", "Generator", {
      name: "writer",
      prompt: "You are an expert writer. Produce clear, well-structured content.",
      showTools: false,
    });
    html += agentGroup("critic", "Critic", {
      name: "critic",
      prompt: "You are a demanding editor. Review drafts for clarity, accuracy, and completeness.",
      showTools: false,
    });
    html += `<label class="form-label">Max Iterations<input class="form-input" id="max-iterations" type="number" value="3" min="1" max="10" /></label>`;
  } else if (currentPattern === "supervisor") {
    html += agentGroup("supervisor", "Supervisor", {
      name: "supervisor",
      prompt: "You manage a team. Route tasks to the right worker based on what's needed.",
      showTools: false,
    });
    html += `<div class="config-group"><div class="config-group-title"><span class="dot" style="background:${PATTERN_COLORS.supervisor}"></span>Workers</div><div id="workers-container"></div><button class="add-worker-btn" id="add-worker-btn">+ Add Worker</button></div>`;
    workerCount = 0;
  }

  configArea.innerHTML = html;

  if (currentPattern === "supervisor") {
    addWorkerCard("researcher", "You are a thorough researcher. Provide detailed, factual analysis.");
    addWorkerCard("writer", "You are a skilled writer. Produce polished, engaging content.");
    document.getElementById("add-worker-btn").addEventListener("click", () => {
      addWorkerCard(`worker_${workerCount + 1}`, "You are a helpful specialist.");
    });
  }
}

function addWorkerCard(name, prompt) {
  workerCount++;
  const idx = workerCount;
  const container = document.getElementById("workers-container");
  const card = document.createElement("div");
  card.className = "worker-card";
  card.id = `worker-card-${idx}`;
  card.innerHTML = `
    <div class="worker-header">
      <span>Worker ${idx}</span>
      <button class="remove-worker" data-idx="${idx}">&times;</button>
    </div>
    <div class="config-form">
      <label class="form-label">Name<input class="form-input" id="worker-${idx}-name" value="${name}" /></label>
      <label class="form-label">System Prompt<textarea class="form-textarea" id="worker-${idx}-prompt" rows="2">${prompt}</textarea></label>
      ${modelSelect(`worker-${idx}-model`, MODELS[0].value)}
      ${toolsCheckboxes(`worker-${idx}`, [])}
    </div>`;
  container.appendChild(card);
  card.querySelector(".remove-worker").addEventListener("click", () => {
    card.remove();
  });
}

// ============================================================
// FLOW DIAGRAM
// ============================================================

function renderFlowDiagram() {
  const color = PATTERN_COLORS[currentPattern];
  let svg = "";

  const W = 140, H = 44, GAP = 70;
  const startR = 14;

  function node(x, y, label, sub = "") {
    return `<rect class="flow-node" x="${x}" y="${y}" width="${W}" height="${H}" stroke="${color}" />
      <text class="flow-label" x="${x + W/2}" y="${y + (sub ? 18 : 24)}" text-anchor="middle">${label}</text>
      ${sub ? `<text class="flow-sublabel" x="${x + W/2}" y="${y + 32}" text-anchor="middle">${sub}</text>` : ""}`;
  }
  function arrow(x1, y1, x2, y2, dashed = false) {
    return `<line class="flow-edge ${dashed ? 'flow-edge-cond' : ''}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" />`;
  }
  function start(cx, cy) {
    return `<circle class="flow-start" cx="${cx}" cy="${cy}" r="${startR}" />
      <text class="flow-sublabel" x="${cx}" y="${cy + 3}" text-anchor="middle">START</text>`;
  }
  function end(cx, cy) {
    return `<circle class="flow-end" cx="${cx}" cy="${cy}" r="${startR}" />
      <text class="flow-sublabel" x="${cx}" y="${cy + 3}" text-anchor="middle">END</text>`;
  }

  if (currentPattern === "react") {
    const svgW = 460, svgH = 180;
    svg = `<svg width="${svgW}" height="${svgH}" viewBox="0 0 ${svgW} ${svgH}">
      <defs><marker id="arrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="${color}"/></marker></defs>
      ${start(30, svgH/2)}
      ${arrow(30 + startR, svgH/2, 80, svgH/2)}
      ${node(80, svgH/2 - H/2, "Agent", "LLM + Tools")}
      ${arrow(80 + W, svgH/2, 80 + W + GAP/2, svgH/2 - 40, true)}
      ${node(80 + W + GAP/2, svgH/2 - 40 - H/2, "Tools", "Execute")}
      ${arrow(80 + W + GAP/2, svgH/2 - 40 + H/2, 80 + W, svgH/2 - 5, true)}
      ${arrow(80 + W, svgH/2, 80 + W + GAP, svgH/2)}
      ${end(80 + W + GAP + startR + 10, svgH/2)}
    </svg>`;
  } else if (currentPattern === "plan_execute") {
    const svgW = 560, svgH = 160;
    svg = `<svg width="${svgW}" height="${svgH}" viewBox="0 0 ${svgW} ${svgH}">
      <defs><marker id="arrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="${color}"/></marker></defs>
      ${start(20, svgH/2)}
      ${arrow(20 + startR, svgH/2, 60, svgH/2)}
      ${node(60, svgH/2 - H/2, "Planner", "Create steps")}
      ${arrow(60 + W, svgH/2, 60 + W + GAP/2, svgH/2)}
      ${node(60 + W + GAP/2, svgH/2 - H/2, "Executor", "Run step")}
      ${arrow(60 + W + GAP/2 + W/2, svgH/2 - H/2, 60 + W + GAP/2 + W/2, svgH/2 - H/2 - 25, true)}
      ${arrow(60 + W + GAP/2 + W/2, svgH/2 - H/2 - 25, 60 + W + GAP/2 + W/2 - 30, svgH/2 - H/2 - 25, true)}
      ${arrow(60 + W + GAP/2 + W/2 - 30, svgH/2 - H/2 - 25, 60 + W + GAP/2 + W/2 - 30, svgH/2 - H/2, true)}
      ${arrow(60 + W + GAP/2 + W, svgH/2, 60 + W + GAP/2 + W + GAP/2, svgH/2)}
      ${node(60 + W + GAP/2 + W + GAP/2, svgH/2 - H/2, "Synthesize", "Final answer")}
      ${arrow(60 + W + GAP/2 + W + GAP/2 + W, svgH/2, 60 + W + GAP/2 + W + GAP/2 + W + 20, svgH/2)}
      ${end(60 + W + GAP/2 + W + GAP/2 + W + 20 + startR + 5, svgH/2)}
    </svg>`;
  } else if (currentPattern === "reflection") {
    const svgW = 440, svgH = 200;
    svg = `<svg width="${svgW}" height="${svgH}" viewBox="0 0 ${svgW} ${svgH}">
      <defs><marker id="arrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="${color}"/></marker></defs>
      ${start(20, svgH/2)}
      ${arrow(20 + startR, svgH/2, 60, svgH/2)}
      ${node(60, svgH/2 - H/2, "Generator", "Create draft")}
      ${arrow(60 + W, svgH/2, 60 + W + GAP, svgH/2)}
      ${node(60 + W + GAP, svgH/2 - H/2, "Critic", "Review draft")}
      ${arrow(60 + W + GAP, svgH/2 + H/2, 60, svgH/2 + H/2, true)}
      ${arrow(60, svgH/2 + H/2, 60, svgH/2 + H/2 - 5, true)}
      ${arrow(60 + W + GAP + W, svgH/2, 60 + W + GAP + W + 20, svgH/2)}
      ${end(60 + W + GAP + W + 20 + startR + 5, svgH/2)}
      <text class="flow-sublabel" x="${60 + W/2}" y="${svgH/2 + H/2 + 15}" text-anchor="middle" fill="${color}">revise</text>
      <text class="flow-sublabel" x="${60 + W + GAP + W + 10}" y="${svgH/2 - 10}" text-anchor="middle" fill="${color}">approved</text>
    </svg>`;
  } else if (currentPattern === "supervisor") {
    const svgW = 440, svgH = 260;
    svg = `<svg width="${svgW}" height="${svgH}" viewBox="0 0 ${svgW} ${svgH}">
      <defs><marker id="arrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="${color}"/></marker></defs>
      ${start(20, 60)}
      ${arrow(20 + startR, 60, 80, 60)}
      ${node(80, 60 - H/2, "Supervisor", "Route tasks")}
      ${arrow(80 + W/3, 60 + H/2, 40, 180)}
      ${node(40, 180 - H/2, "Worker 1", "Specialist")}
      ${arrow(40 + W, 180, 80 + W/3, 60 + H/2, true)}
      ${arrow(80 + W*2/3, 60 + H/2, 240, 180)}
      ${node(240, 180 - H/2, "Worker 2", "Specialist")}
      ${arrow(240, 180, 80 + W*2/3, 60 + H/2, true)}
      ${arrow(80 + W, 60, 80 + W + GAP/2, 60)}
      ${node(80 + W + GAP/2, 60 - H/2, "Synthesize", "Final answer")}
      ${arrow(80 + W + GAP/2 + W, 60, 80 + W + GAP/2 + W + 15, 60)}
      ${end(80 + W + GAP/2 + W + 15 + startR + 5, 60)}
    </svg>`;
  }

  flowCanvas.innerHTML = svg;
}

// ============================================================
// BUILD CONFIG FROM FORM
// ============================================================

function getVal(id) {
  const el = document.getElementById(id);
  return el ? el.value : "";
}

function getCheckedTools(group) {
  const boxes = document.querySelectorAll(`input[data-tool-group="${group}"]:checked`);
  return Array.from(boxes).map(cb => ({ name: cb.value, description: `${cb.value} tool` }));
}

function buildConfig() {
  const config = {
    name: getVal("agent-name") || "my-agent",
    description: getVal("agent-desc") || "",
    pattern: currentPattern,
  };

  if (currentPattern === "react") {
    config.agent = {
      name: getVal("agent-name") || "agent",
      system_prompt: getVal("agent-prompt"),
      model: getVal("agent-model"),
      tools: getCheckedTools("agent"),
    };
  } else if (currentPattern === "plan_execute") {
    config.planner = {
      name: getVal("planner-name") || "planner",
      system_prompt: getVal("planner-prompt"),
      model: getVal("planner-model"),
      tools: [],
    };
    config.executor = {
      name: getVal("executor-name") || "executor",
      system_prompt: getVal("executor-prompt"),
      model: getVal("executor-model"),
      tools: getCheckedTools("executor"),
    };
  } else if (currentPattern === "reflection") {
    config.generator = {
      name: getVal("generator-name") || "writer",
      system_prompt: getVal("generator-prompt"),
      model: getVal("generator-model"),
      tools: [],
    };
    config.critic = {
      name: getVal("critic-name") || "critic",
      system_prompt: getVal("critic-prompt"),
      model: getVal("critic-model"),
      tools: [],
    };
    config.max_iterations = parseInt(getVal("max-iterations")) || 3;
  } else if (currentPattern === "supervisor") {
    config.supervisor = {
      name: getVal("supervisor-name") || "supervisor",
      system_prompt: getVal("supervisor-prompt"),
      model: getVal("supervisor-model"),
      tools: [],
    };
    config.workers = [];
    document.querySelectorAll("[id^='worker-card-']").forEach(card => {
      const idx = card.id.split("-").pop();
      config.workers.push({
        name: getVal(`worker-${idx}-name`) || `worker_${idx}`,
        system_prompt: getVal(`worker-${idx}-prompt`),
        model: getVal(`worker-${idx}-model`),
        tools: getCheckedTools(`worker-${idx}`),
      });
    });
  }

  return config;
}

// ============================================================
// BUILD & TEST
// ============================================================

document.getElementById("build-btn").addEventListener("click", async () => {
  const btn = document.getElementById("build-btn");
  const config = buildConfig();

  btn.disabled = true;
  btn.textContent = "Building...";

  try {
    const res = await fetch(`${API}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ config }),
    });

    if (!res.ok) {
      const err = await res.json();
      alert(`Build failed: ${err.detail}`);
      btn.disabled = false;
      btn.textContent = "Build & Test Agent";
      return;
    }

    const data = await res.json();
    sessionId = data.session_id;

    chatTitle.textContent = data.agent_name;
    sessionBadge.textContent = `${data.pattern} | ${sessionId}`;
    sessionBadge.style.display = "";
    emptyState.style.display = "none";
    chatArea.innerHTML = "";

    stepTrace.style.display = "";
    traceList.innerHTML = '<div class="trace-item"><span class="trace-dot done"></span>Agent compiled successfully</div>';

    msgInput.disabled = false;
    sendBtn.disabled = false;
    msgInput.focus();
  } catch (e) {
    alert(`Error: ${e.message}`);
  }

  btn.disabled = false;
  btn.textContent = "Build & Test Agent";
});

// ============================================================
// STREAMING CHAT
// ============================================================

async function sendMessage() {
  const text = msgInput.value.trim();
  if (!text || !sessionId) return;

  appendMessage("user", text);
  msgInput.value = "";
  msgInput.disabled = true;
  sendBtn.disabled = true;
  traceList.innerHTML = "";

  const assistantEl = appendMessage("assistant", "");
  const contentEl = assistantEl.querySelector(".content");
  contentEl.innerHTML = '<span class="streaming-cursor"></span>';

  let fullText = "";

  try {
    const res = await fetch(`${API}/sessions/${sessionId}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith("event:")) {
          const eventType = line.slice(6).trim();
          continue;
        }
        if (!line.startsWith("data:")) continue;

        const raw = line.slice(5).trim();
        if (!raw) continue;

        let data;
        try { data = JSON.parse(raw); } catch { continue; }

        // We need the event type — parse from the preceding event: line
        // SSE format: event: xxx\ndata: {...}\n\n
        // Since we process line-by-line, track event type
      }

      // Re-parse with event tracking
      const events = parseSSE(buffer + lines.join("\n"));
      // Actually let's use a simpler approach
    }
  } catch (e) {
    // Fallback: non-streaming
  }

  // Fallback to non-streaming if SSE didn't work
  if (!fullText) {
    try {
      const res = await fetch(`${API}/sessions/${sessionId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      fullText = data.response;

      // Show steps in trace
      if (data.steps) {
        traceList.innerHTML = "";
        for (const step of data.steps) {
          if (step.tool_calls) {
            for (const tc of step.tool_calls) {
              addTraceItem("tool", `Tool: ${tc.name}(${JSON.stringify(tc.args).slice(0, 60)})`);
            }
          }
        }
      }
    } catch (e) {
      fullText = `Error: ${e.message}`;
    }
  }

  contentEl.textContent = fullText;
  msgInput.disabled = false;
  sendBtn.disabled = false;
  msgInput.focus();
  chatArea.scrollTop = chatArea.scrollHeight;
}

// SSE streaming with proper event parsing
async function sendMessageStreaming() {
  const text = msgInput.value.trim();
  if (!text || !sessionId) return;

  appendMessage("user", text);
  msgInput.value = "";
  msgInput.disabled = true;
  sendBtn.disabled = true;
  traceList.innerHTML = "";

  const assistantEl = appendMessage("assistant", "");
  const contentEl = assistantEl.querySelector(".content");
  contentEl.innerHTML = '<span class="streaming-cursor"></span>';

  let fullText = "";
  let currentEvent = "";

  try {
    const response = await fetch(`${API}/sessions/${sessionId}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      while (buffer.includes("\n")) {
        const idx = buffer.indexOf("\n");
        const line = buffer.slice(0, idx).trim();
        buffer = buffer.slice(idx + 1);

        if (line.startsWith("event:")) {
          currentEvent = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
          const raw = line.slice(5).trim();
          if (!raw) continue;
          let data;
          try { data = JSON.parse(raw); } catch { continue; }

          if (currentEvent === "token" && data.token) {
            fullText += data.token;
            contentEl.textContent = fullText;
            chatArea.scrollTop = chatArea.scrollHeight;
          } else if (currentEvent === "node_start" && data.node) {
            addTraceItem("node", `Node: ${data.node}`);
          } else if (currentEvent === "tool_call" && data.tool) {
            addTraceItem("tool", `Tool: ${data.tool}`);
          } else if (currentEvent === "tool_result" && data.result) {
            addTraceItem("done", `Result: ${data.result.slice(0, 80)}`);
          } else if (currentEvent === "done" && data.response) {
            fullText = data.response;
            contentEl.textContent = fullText;
          } else if (currentEvent === "error") {
            contentEl.textContent = `Error: ${data.error}`;
          }
        }
      }
    }

    if (!fullText) {
      contentEl.textContent = "(No response)";
    }
  } catch (e) {
    // Fallback to non-streaming
    try {
      const res = await fetch(`${API}/sessions/${sessionId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      fullText = data.response;
      contentEl.textContent = fullText;
    } catch (e2) {
      contentEl.textContent = `Error: ${e2.message}`;
    }
  }

  msgInput.disabled = false;
  sendBtn.disabled = false;
  msgInput.focus();
  chatArea.scrollTop = chatArea.scrollHeight;
}

sendBtn.addEventListener("click", sendMessageStreaming);
msgInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessageStreaming(); }
});

function addTraceItem(type, text) {
  const item = document.createElement("div");
  item.className = "trace-item";
  item.innerHTML = `<span class="trace-dot ${type}"></span>${escapeHtml(text)}`;
  traceList.appendChild(item);
  stepTrace.scrollTop = stepTrace.scrollHeight;
}

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

// ============================================================
// PRESETS
// ============================================================

async function loadPresets() {
  try {
    const res = await fetch(`${API}/presets`);
    const presets = await res.json();
    const list = document.getElementById("preset-list");
    list.innerHTML = "";

    for (const [name, cfg] of Object.entries(presets)) {
      const pColor = PATTERN_COLORS[cfg.pattern] || "#888";
      const card = document.createElement("div");
      card.className = "preset-card";
      card.innerHTML = `<span class="preset-pattern" style="background:${pColor}">${cfg.pattern}</span><h4>${cfg.name}</h4><p>${cfg.description}</p>`;
      card.addEventListener("click", () => loadPreset(cfg));
      list.appendChild(card);
    }
  } catch (e) { /* server not ready */ }
}

function loadPreset(cfg) {
  currentPattern = cfg.pattern;
  document.querySelectorAll(".pattern-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.pattern === currentPattern);
  });
  flowBadge.textContent = PATTERN_LABELS[currentPattern];
  flowBadge.style.background = PATTERN_COLORS[currentPattern];

  renderConfigForm();
  renderFlowDiagram();

  // Fill in values
  const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.value = val || ""; };
  setVal("agent-name", cfg.name);
  setVal("agent-desc", cfg.description);

  if (cfg.agent) {
    setVal("agent-name", cfg.agent.name);
    setVal("agent-prompt", cfg.agent.system_prompt);
    setVal("agent-model", cfg.agent.model);
    checkTools("agent", cfg.agent.tools);
  }
  if (cfg.planner) {
    setVal("planner-name", cfg.planner.name);
    setVal("planner-prompt", cfg.planner.system_prompt);
    setVal("planner-model", cfg.planner.model);
  }
  if (cfg.executor) {
    setVal("executor-name", cfg.executor.name);
    setVal("executor-prompt", cfg.executor.system_prompt);
    setVal("executor-model", cfg.executor.model);
    checkTools("executor", cfg.executor.tools);
  }
  if (cfg.generator) {
    setVal("generator-name", cfg.generator.name);
    setVal("generator-prompt", cfg.generator.system_prompt);
    setVal("generator-model", cfg.generator.model);
  }
  if (cfg.critic) {
    setVal("critic-name", cfg.critic.name);
    setVal("critic-prompt", cfg.critic.system_prompt);
    setVal("critic-model", cfg.critic.model);
  }
  if (cfg.max_iterations) setVal("max-iterations", cfg.max_iterations);
  if (cfg.supervisor) {
    setVal("supervisor-name", cfg.supervisor.name);
    setVal("supervisor-prompt", cfg.supervisor.system_prompt);
    setVal("supervisor-model", cfg.supervisor.model);
  }
}

function checkTools(group, tools) {
  if (!tools) return;
  const names = tools.map(t => t.name);
  document.querySelectorAll(`input[data-tool-group="${group}"]`).forEach(cb => {
    cb.checked = names.includes(cb.value);
  });
}

// ============================================================
// EXPORT
// ============================================================

document.getElementById("export-json-btn").addEventListener("click", () => {
  const config = buildConfig();
  modalTitle.textContent = "Agent Config (JSON)";
  exportContent.value = JSON.stringify(config, null, 2);
  exportModal.style.display = "";
});

document.getElementById("export-py-btn").addEventListener("click", async () => {
  const config = buildConfig();
  try {
    const res = await fetch(`${API}/export/python`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    const data = await res.json();
    modalTitle.textContent = "Agent Code (Python)";
    exportContent.value = data.code;
    exportModal.style.display = "";
  } catch (e) {
    alert(`Export failed: ${e.message}`);
  }
});

document.getElementById("modal-close").addEventListener("click", () => { exportModal.style.display = "none"; });
exportModal.addEventListener("click", (e) => { if (e.target === exportModal) exportModal.style.display = "none"; });
document.getElementById("copy-btn").addEventListener("click", () => {
  navigator.clipboard.writeText(exportContent.value);
  document.getElementById("copy-btn").textContent = "Copied!";
  setTimeout(() => { document.getElementById("copy-btn").textContent = "Copy to Clipboard"; }, 1500);
});

// ============================================================
// INIT
// ============================================================

renderConfigForm();
renderFlowDiagram();
loadPresets();
