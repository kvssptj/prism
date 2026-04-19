// === State ===
const state = {
  currentView: 'split',
  thoughtsVisible: true,
  personas: {},
  perspectiveCount: 0,
  dialogueCount: 0,
  currentScenarioFile: null,
};

// === LLM Settings ===
const DEFAULT_LLM_SETTINGS = {
  provider: 'none',
  claudeApiKey: '',
  openaiApiKey: '',
  openaiModel: 'gpt-4o',
  ollamaUrl: 'http://localhost:11434',
  ollamaModel: 'llama3',
  domain: 'product management at a B2B SaaS company',
};
let llmSettings = (() => {
  try { return JSON.parse(localStorage.getItem('perspective_settings') || 'null') || { ...DEFAULT_LLM_SETTINGS }; }
  catch { return { ...DEFAULT_LLM_SETTINGS }; }
})();
function saveSettings(u) {
  llmSettings = { ...llmSettings, ...u };
  localStorage.setItem('perspective_settings', JSON.stringify(llmSettings));
}
function buildSettingsHeader() {
  return btoa(JSON.stringify(llmSettings));
}

const PROVIDER_LABELS = {
  none: 'Templates',
  claude: 'Claude API',
  openai: 'OpenAI',
  ollama: 'Ollama',
  claude_code: 'Claude Code',
};

// === DOM refs ===
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const els = {
  title: $('#scenarioTitle'),
  meta: $('#scenarioMeta'),
  personaBar: $('#personaBar'),
  emptyState: $('#emptyState'),
  splitView: $('#splitView'),
  dialogueView: $('#dialogueView'),
  content: $('#content'),
  scenarioList: $('#scenarioList'),
  sidebar: $('#sidebar'),
};

// === Color map for persona bubbles ===
const personaColors = {};

function getPersonaBubbleColor(hex) {
  // Return a light tinted background for message bubbles
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, 0.06)`;
}

function getPersonaBorderColor(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, 0.18)`;
}

// === WebSocket ===
let ws;

function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws`);
  ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    handleChunk(data);
  };
  ws.onclose = () => setTimeout(connectWS, 2000);
}

function handleChunk(chunk) {
  switch (chunk.type) {
    case 'metadata':
      renderMetadata(chunk);
      break;
    case 'perspective':
      renderPerspective(chunk);
      break;
    case 'dialogue':
      renderDialogue(chunk);
      break;
  }
}

// === Render metadata ===
function renderMetadata(data) {
  // Reset
  state.perspectiveCount = 0;
  state.dialogueCount = 0;
  state.personas = {};
  els.splitView.innerHTML = '';
  els.dialogueView.innerHTML = '';

  els.title.textContent = data.title;
  els.meta.textContent = `${data.personas.length} perspectives · ${data.mode} mode`;
  els.emptyState.classList.add('hidden');
  updateViewVisibility();

  // Personas
  els.personaBar.innerHTML = '';
  data.personas.forEach((p) => {
    state.personas[p.id] = p;
    const chip = document.createElement('span');
    chip.className = 'persona-chip';
    chip.setAttribute('role', 'listitem');
    chip.innerHTML = `<span class="persona-dot" style="background:${p.color}"></span>${p.name}`;
    els.personaBar.appendChild(chip);
  });
}

// === Render perspective (split panel) ===
function renderPerspective(data) {
  const persona = state.personas[data.persona_id];
  if (!persona) return;

  state.perspectiveCount++;
  const delay = (state.perspectiveCount - 1) * 0.15;

  const panel = document.createElement('div');
  panel.className = 'panel';
  panel.style.setProperty('--panel-color', persona.color);
  panel.style.animationDelay = `${delay}s`;
  panel.innerHTML = `
    <div class="panel-header">
      <div class="avatar" style="background:${persona.color}">${persona.avatar}</div>
      <div>
        <div class="panel-name">${persona.name}</div>
        <div class="panel-role">${persona.role}</div>
      </div>
    </div>
    <div class="panel-body">${data.thinking}</div>
    <div class="panel-tag">
      <div class="tag-label">${data.tag_label}</div>
      <div class="tag-content">${data.tag_content}</div>
    </div>
  `;

  els.splitView.appendChild(panel);
  updateViewVisibility();
}

// === Render dialogue message ===
function renderDialogue(data) {
  const persona = state.personas[data.persona_id];
  if (!persona) return;

  // Remove typing indicator if present
  const typing = els.dialogueView.querySelector('.typing-indicator');
  if (typing) typing.remove();

  state.dialogueCount++;

  const msg = document.createElement('div');
  msg.className = 'message';
  msg.innerHTML = `
    <div class="avatar" style="background:${persona.color}">${persona.avatar}</div>
    <div class="message-content">
      <div class="message-name" style="color:${persona.color}">${persona.name}</div>
      <div class="message-bubble" style="background:${getPersonaBubbleColor(persona.color)};border-color:${getPersonaBorderColor(persona.color)}">
        "${data.said}"
      </div>
      <div class="inner-thought" style="--thought-color:${persona.color}" onclick="this.classList.toggle('collapsed')" role="button" tabindex="0" aria-label="Toggle inner thought">
        <div class="thought-label">
          <span class="chevron">&#9660;</span> Inner thought
        </div>
        <div class="thought-body">${data.thought}</div>
      </div>
    </div>
  `;

  els.dialogueView.appendChild(msg);

  // Add typing indicator for next message
  addTypingIndicator();

  // Scroll to bottom
  els.content.scrollTop = els.content.scrollHeight;
  updateViewVisibility();
}

function addTypingIndicator() {
  const existing = els.dialogueView.querySelector('.typing-indicator');
  if (existing) existing.remove();

  const indicator = document.createElement('div');
  indicator.className = 'typing-indicator';
  indicator.innerHTML = `
    <div class="avatar" style="background:var(--text-tertiary);width:36px;height:36px;border-radius:10px"></div>
    <div class="typing-dots"><span></span><span></span><span></span></div>
  `;
  els.dialogueView.appendChild(indicator);
}

// === View management ===
function updateViewVisibility() {
  const view = state.currentView;
  const hasPerspectives = state.perspectiveCount > 0;
  const hasDialogue = state.dialogueCount > 0;
  const hasContent = hasPerspectives || hasDialogue;

  els.emptyState.classList.toggle('hidden', hasContent);

  if (view === 'split') {
    els.splitView.classList.toggle('hidden', !hasPerspectives);
    els.dialogueView.classList.add('hidden');
  } else if (view === 'dialogue') {
    els.splitView.classList.add('hidden');
    els.dialogueView.classList.toggle('hidden', !hasDialogue);
  } else {
    // both
    els.splitView.classList.toggle('hidden', !hasPerspectives);
    els.dialogueView.classList.toggle('hidden', !hasDialogue);

    // Add divider between split and dialogue if both have content
    if (hasPerspectives && hasDialogue) {
      const existingDivider = els.content.querySelector('.section-divider');
      if (!existingDivider) {
        const divider = document.createElement('div');
        divider.className = 'section-divider';
        divider.textContent = 'Conversation';
        els.content.insertBefore(divider, els.dialogueView);
      }
    }
  }
}

function setView(view) {
  state.currentView = view;
  selectedMode = view;
  $$('.view-btn').forEach((btn) => {
    const isActive = btn.dataset.view === view;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-selected', isActive);
  });
  updateViewVisibility();
}

// === Sidebar ===
function formatRelativeTime(filename) {
  // Extract timestamp from filename pattern like _17764394 (unix-ish) or date patterns
  const match = filename.match(/(\d{8,})/);
  if (!match) return '';
  const num = match[1];
  // If it looks like a unix timestamp (10 digits), convert
  if (num.length >= 10) {
    const ts = parseInt(num.slice(0, 10), 10) * 1000;
    const diff = Date.now() - ts;
    if (diff < 0 || diff > 365 * 24 * 60 * 60 * 1000) return '';
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return `${Math.floor(diff / 86400000)}d ago`;
  }
  return '';
}

async function loadScenarioList() {
  try {
    const res = await fetch('/scenarios');
    const scenarios = await res.json();
    els.scenarioList.innerHTML = '';
    scenarios.forEach((s) => {
      const li = document.createElement('li');
      li.setAttribute('role', 'listitem');
      li.setAttribute('tabindex', '0');
      li.dataset.filename = s.filename;
      const timeLabel = formatRelativeTime(s.filename);
      li.innerHTML = `
        <span class="scenario-list-title">${s.title}</span>
        ${timeLabel ? `<span class="scenario-list-meta">${timeLabel}</span>` : ''}
      `;
      li.addEventListener('click', () => loadScenario(s.filename));
      li.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          loadScenario(s.filename);
        }
      });
      els.scenarioList.appendChild(li);
    });
  } catch (err) {
    console.error('Failed to load scenarios:', err);
  }
}

async function loadScenario(filename) {
  state.currentScenarioFile = filename;

  // Highlight active
  els.scenarioList.querySelectorAll('li').forEach((li) => {
    li.classList.toggle('active', li.dataset.filename === filename);
  });

  try {
    const res = await fetch(`/scenarios/${filename}`);
    const data = await res.json();
    replayScenario(data);
  } catch (err) {
    console.error('Failed to load scenario:', err);
  }
}

async function replayScenario(data) {
  // Send metadata
  renderMetadata({
    type: 'metadata',
    ...data,
  });

  // Replay perspectives with delay
  for (const p of data.perspectives || []) {
    await sleep(400);
    renderPerspective(p);
  }

  // Replay dialogue with delay
  for (const d of data.dialogue || []) {
    await sleep(600);
    renderDialogue(d);
  }

  // Remove final typing indicator
  const typing = els.dialogueView.querySelector('.typing-indicator');
  if (typing) typing.remove();
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

// === Input Form ===

const PRESETS = {
  'feature-scope': {
    text: 'We\'re cutting a key feature from the upcoming release to hit the deadline. It was prominently featured in the sales deck and customer demos.',
    personas: ['pm', 'eng', 'sales', 'cs', 'design'],
  },
  'escalation': {
    text: 'Our largest enterprise customer is threatening to churn at renewal unless we build a capability that isn\'t on the roadmap. The deal is worth significant ARR.',
    personas: ['cs', 'sales', 'pm', 'eng', 'exec'],
  },
  'launch': {
    text: 'Engineering says they need two more weeks for critical fixes. Marketing already announced the launch date publicly. Leadership is asking if we\'re ready to ship.',
    personas: ['pm', 'eng', 'design', 'sales', 'exec'],
  },
  'build-buy': {
    text: 'We need a capability that exists in the market as a third-party service. Engineering wants to build it in-house for better integration. Finance wants to buy and move fast.',
    personas: ['pm', 'eng', 'sc', 'exec'],
  },
  'research': {
    text: 'User research shows our most-requested feature is actually used by less than 5% of customers. We just spent three sprints rebuilding it based on the request volume.',
    personas: ['uxr', 'pm', 'eng', 'design'],
  },
  'discovery': {
    text: 'During discovery interviews, we found a user persona we didn\'t account for. They have different needs than our primary users and represent a growing segment of the market.',
    personas: ['uxr', 'pm', 'design', 'eng', 'sales'],
  },
};

let selectedPersonas = new Set(['pm', 'eng', 'sales', 'cs']);
let selectedMode = 'both';
let allPersonas = [];
let selectedCustomColor = '#0B2B1B';

// === Context ===
const DEFAULT_CONTEXT = { stage: 'series_a', market: 'b2b', deadline: 'this_week' };
let scenarioContext = (() => {
  try { return JSON.parse(localStorage.getItem('perspective_context')) || { ...DEFAULT_CONTEXT }; }
  catch { return { ...DEFAULT_CONTEXT }; }
})();

const CTX_LABELS = {
  stage:    { seed: 'Seed', series_a: 'Series A', series_b: 'Series B', growth: 'Growth', enterprise: 'Enterprise' },
  market:   { b2b: 'B2B', b2c: 'B2C', b2b2c: 'B2B2C' },
  deadline: { today: 'Today', this_week: 'This week', this_month: 'This month', no_rush: 'No rush' },
};

function updateContextSummary() {
  const el = document.getElementById('ctxSummary');
  if (!el) return;
  const stage    = CTX_LABELS.stage[scenarioContext.stage]    || scenarioContext.stage;
  const market   = CTX_LABELS.market[scenarioContext.market]   || scenarioContext.market;
  const deadline = CTX_LABELS.deadline[scenarioContext.deadline] || scenarioContext.deadline;
  el.textContent = `${stage} · ${market} · ${deadline}`;
}

function initContext() {
  const groupMap = { ctxStage: 'stage', ctxMarket: 'market', ctxDeadline: 'deadline' };
  Object.entries(groupMap).forEach(([groupId, key]) => {
    const group = document.getElementById(groupId);
    if (!group) return;
    group.querySelectorAll('.ctx-btn').forEach((btn) => {
      btn.classList.toggle('selected', btn.dataset.value === scenarioContext[key]);
    });
    group.querySelectorAll('.ctx-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        group.querySelectorAll('.ctx-btn').forEach((b) => b.classList.remove('selected'));
        btn.classList.add('selected');
        scenarioContext[key] = btn.dataset.value;
        localStorage.setItem('perspective_context', JSON.stringify(scenarioContext));
        updateContextSummary();
      });
    });
  });

  updateContextSummary();

  // Toggle panel open/close
  const btn   = document.getElementById('ctxSettingsBtn');
  const panel = document.getElementById('ctxSettingsPanel');
  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    panel.classList.toggle('hidden');
    btn.classList.toggle('active', !panel.classList.contains('hidden'));
  });

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!document.getElementById('ctxSettingsWrap').contains(e.target)) {
      panel.classList.add('hidden');
      btn.classList.remove('active');
    }
  });
}

async function initInputForm() {
  // Load personas from server
  try {
    const res = await fetch('/personas');
    allPersonas = await res.json();
  } catch (e) {
    allPersonas = [];
  }
  renderPersonaChips();
}

function renderPersonaChips() {
  const container = $('#personaChips');
  container.innerHTML = '';
  allPersonas.forEach((p) => {
    const chip = document.createElement('button');
    chip.className = `p-chip ${selectedPersonas.has(p.id) ? 'selected' : ''}`;
    chip.setAttribute('tabindex', '0');
    chip.innerHTML = `<span class="chip-dot" style="background:${p.color}"></span>${p.name}`;
    chip.addEventListener('click', () => {
      if (selectedPersonas.has(p.id)) {
        selectedPersonas.delete(p.id);
      } else {
        selectedPersonas.add(p.id);
      }
      chip.classList.toggle('selected');
    });
    container.appendChild(chip);
  });
}

// Presets
$$('.preset-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    const preset = PRESETS[btn.dataset.preset];
    if (!preset) return;

    // Toggle active preset
    $$('.preset-btn').forEach((b) => b.classList.remove('active'));
    btn.classList.add('active');

    $('#scenarioInput').value = preset.text;
    selectedPersonas = new Set(preset.personas);
    renderPersonaChips();
  });
});

// Chat options toggle handled via inline onclick on #inputToggle

// Custom persona form
$('#addPersonaBtn').addEventListener('click', () => {
  $('#customPersonaForm').classList.remove('hidden');
  $('#customName').focus();
});

$('#cancelPersona').addEventListener('click', () => {
  $('#customPersonaForm').classList.add('hidden');
  $('#customName').value = '';
  $('#customRole').value = '';
});

// Color picker
$$('.color-swatch').forEach((swatch) => {
  swatch.addEventListener('click', () => {
    $$('.color-swatch').forEach((s) => s.classList.remove('active'));
    swatch.classList.add('active');
    selectedCustomColor = swatch.dataset.color;
  });
  swatch.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      swatch.click();
    }
  });
});

// Save custom persona
$('#savePersona').addEventListener('click', async () => {
  const name = $('#customName').value.trim();
  const role = $('#customRole').value.trim();
  if (!name) return;

  const id = name.toLowerCase().replace(/[^a-z0-9]+/g, '_');
  const avatar = name.slice(0, 2).toUpperCase();
  const persona = { id, name, role: role || 'Stakeholder', color: selectedCustomColor, avatar };

  try {
    await fetch('/personas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(persona),
    });

    allPersonas.push({ ...persona, custom: true });
    selectedPersonas.add(id);
    renderPersonaChips();

    $('#customPersonaForm').classList.add('hidden');
    $('#customName').value = '';
    $('#customRole').value = '';
  } catch (e) {
    console.error('Failed to save persona:', e);
  }
});

// Generate button
$('#btnGenerate').addEventListener('click', async () => {
  const scenario = $('#scenarioInput').value.trim();
  if (!scenario) {
    $('#scenarioInput').focus();
    return;
  }

  const btn = $('#btnGenerate');
  btn.disabled = true;
  btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-dasharray="40" stroke-dashoffset="40" style="animation:spin 0.8s linear infinite"><circle cx="12" cy="12" r="10"/></svg>';

  // Collect custom persona details for selected custom personas
  const customPersonas = allPersonas
    .filter((p) => p.custom && selectedPersonas.has(p.id))
    .map(({ custom, ...rest }) => rest);

  try {
    await fetch('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-LLM-Settings': buildSettingsHeader() },
      body: JSON.stringify({
        scenario,
        personas: Array.from(selectedPersonas),
        custom_personas: customPersonas,
        mode: selectedMode,
        context: scenarioContext,
      }),
    });

    // Close the options panel
    const panel = $('#inputPanel');
    const toggleBtn = $('#inputToggle');
    if (panel) { panel.classList.remove('open'); }
    if (toggleBtn) { toggleBtn.setAttribute('aria-expanded', 'false'); }

    showStatus('Generating perspectives...', 'info');

    // Refresh sidebar after a delay
    setTimeout(loadScenarioList, 3000);
  } catch (e) {
    console.error('Generate failed:', e);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>';
  }
});

// Queue button
$('#btnQueue').addEventListener('click', async () => {
  const scenario = $('#scenarioInput').value.trim();
  if (!scenario) {
    $('#scenarioInput').focus();
    return;
  }

  const btn = $('#btnQueue');
  btn.disabled = true;

  const customPersonas = allPersonas
    .filter((p) => p.custom && selectedPersonas.has(p.id))
    .map(({ custom, ...rest }) => rest);

  try {
    await fetch('/queue', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario,
        personas: Array.from(selectedPersonas),
        custom_personas: customPersonas,
        mode: selectedMode,
        context: scenarioContext,
      }),
    });

    showStatus('Sent to Claude Code — generating...', 'success');
  } catch (e) {
    console.error('Queue failed:', e);
  } finally {
    btn.disabled = false;
  }
});

function showStatus(msg, type) {
  // Remove existing status
  const existing = $('.status-msg');
  if (existing) existing.remove();

  const el = document.createElement('div');
  el.className = `status-msg ${type}`;
  el.textContent = msg;

  const actions = $('.input-actions');
  if (actions) actions.after(el);

  setTimeout(() => el.remove(), 5000);
}

// === Event listeners ===
$$('.view-btn').forEach((btn) => {
  btn.addEventListener('click', () => setView(btn.dataset.view));
});

$('#thoughtsToggle').addEventListener('click', function () {
  state.thoughtsVisible = !state.thoughtsVisible;
  this.setAttribute('aria-pressed', state.thoughtsVisible);
  document.body.classList.toggle('thoughts-hidden', !state.thoughtsVisible);
});

$('#sidebarToggle').addEventListener('click', () => {
  els.sidebar.classList.add('collapsed');
});

$('#sidebarOpen').addEventListener('click', () => {
  els.sidebar.classList.remove('collapsed');
});

// Keyboard: Enter/Space on inner-thought
document.addEventListener('keydown', (e) => {
  if ((e.key === 'Enter' || e.key === ' ') && e.target.classList.contains('inner-thought')) {
    e.preventDefault();
    e.target.classList.toggle('collapsed');
  }
});

// === Textarea auto-resize ===
const chatTextarea = $('#scenarioInput');
chatTextarea.addEventListener('input', () => {
  chatTextarea.style.height = 'auto';
  const h = chatTextarea.scrollHeight;
  chatTextarea.style.height = Math.min(h, 240) + 'px';
  chatTextarea.style.overflow = h > 240 ? 'auto' : 'hidden';
});

// Cmd/Ctrl+Enter to generate
chatTextarea.addEventListener('keydown', (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
    e.preventDefault();
    $('#btnGenerate').click();
  }
});

function initSettings() {
  const btn = document.getElementById('llmSettingsBtn');
  const panel = document.getElementById('llmSettingsPanel');
  const providerLabel = document.getElementById('llmProviderLabel');

  function showProviderConfig(provider) {
    document.querySelectorAll('.provider-config').forEach((el) => el.classList.add('hidden'));
    const domainRow = document.getElementById('domainRow');
    if (provider === 'claude') {
      document.getElementById('configClaude').classList.remove('hidden');
      domainRow.classList.remove('hidden');
    } else if (provider === 'openai') {
      document.getElementById('configOpenai').classList.remove('hidden');
      domainRow.classList.remove('hidden');
    } else if (provider === 'ollama') {
      document.getElementById('configOllama').classList.remove('hidden');
      domainRow.classList.remove('hidden');
    } else if (provider === 'claude_code') {
      document.getElementById('configClaudeCode').classList.remove('hidden');
      domainRow.classList.remove('hidden');
    } else {
      domainRow.classList.add('hidden');
    }
  }

  function updateBtnState(provider) {
    providerLabel.textContent = PROVIDER_LABELS[provider] || 'Templates';
    btn.classList.toggle('has-provider', provider !== 'none');
  }

  // Set initial radio state
  const radios = document.querySelectorAll('input[name="llmProvider"]');
  radios.forEach((radio) => {
    if (radio.value === llmSettings.provider) radio.checked = true;
    radio.addEventListener('change', () => {
      saveSettings({ provider: radio.value });
      showProviderConfig(radio.value);
      updateBtnState(radio.value);
    });
  });

  // Set initial config values
  const claudeKey = document.getElementById('claudeApiKey');
  if (claudeKey) {
    claudeKey.value = llmSettings.claudeApiKey || '';
    claudeKey.addEventListener('input', () => saveSettings({ claudeApiKey: claudeKey.value }));
  }
  const openaiKey = document.getElementById('openaiApiKey');
  if (openaiKey) {
    openaiKey.value = llmSettings.openaiApiKey || '';
    openaiKey.addEventListener('input', () => saveSettings({ openaiApiKey: openaiKey.value }));
  }
  const openaiModel = document.getElementById('openaiModel');
  if (openaiModel) {
    openaiModel.value = llmSettings.openaiModel || 'gpt-4o';
    openaiModel.addEventListener('change', () => saveSettings({ openaiModel: openaiModel.value }));
  }
  const ollamaUrl = document.getElementById('ollamaUrl');
  if (ollamaUrl) {
    ollamaUrl.value = llmSettings.ollamaUrl || 'http://localhost:11434';
    ollamaUrl.addEventListener('input', () => saveSettings({ ollamaUrl: ollamaUrl.value }));
  }
  const ollamaModel = document.getElementById('ollamaModel');
  if (ollamaModel) {
    ollamaModel.value = llmSettings.ollamaModel || 'llama3';
    ollamaModel.addEventListener('change', () => saveSettings({ ollamaModel: ollamaModel.value }));
  }
  const domainInput = document.getElementById('domainInput');
  if (domainInput) {
    domainInput.value = llmSettings.domain || DEFAULT_LLM_SETTINGS.domain;
    domainInput.addEventListener('input', () => saveSettings({ domain: domainInput.value }));
  }

  // Refresh Ollama models
  const refreshBtn = document.getElementById('refreshOllamaModels');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', async () => {
      refreshBtn.disabled = true;
      refreshBtn.textContent = '...';
      try {
        const url = (document.getElementById('ollamaUrl').value || 'http://localhost:11434').trim();
        const res = await fetch(`/ollama/models?url=${encodeURIComponent(url)}`);
        const data = await res.json();
        if (data.models && data.models.length > 0) {
          ollamaModel.innerHTML = '';
          data.models.forEach((m) => {
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = m;
            if (m === llmSettings.ollamaModel) opt.selected = true;
            ollamaModel.appendChild(opt);
          });
        }
      } catch (e) {
        console.error('Failed to refresh Ollama models:', e);
      } finally {
        refreshBtn.disabled = false;
        refreshBtn.textContent = 'Refresh';
      }
    });
  }

  // Apply initial state
  showProviderConfig(llmSettings.provider);
  updateBtnState(llmSettings.provider);

  // Toggle panel
  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    panel.classList.toggle('hidden');
    btn.classList.toggle('active', !panel.classList.contains('hidden'));
  });

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!document.getElementById('llmSettingsWrap').contains(e.target)) {
      panel.classList.add('hidden');
      btn.classList.remove('active');
    }
  });
}

// === Init ===
connectWS();
loadScenarioList();
initInputForm();
initContext();
initSettings();
