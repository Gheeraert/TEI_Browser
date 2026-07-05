const state = {
  filePath: null,
  htmlPath: null,
  htmlUrl: null,
  profile: "prose",
  lastPayload: null,
};

const els = {
  openFile: document.querySelector("#open-file"),
  currentFile: document.querySelector("#current-file"),
  profile: document.querySelector("#profile"),
  render: document.querySelector("#render"),
  inspect: document.querySelector("#inspect"),
  openExternal: document.querySelector("#open-external"),
  reload: document.querySelector("#reload"),
  preview: document.querySelector("#preview"),
  emptyPreview: document.querySelector("#empty-preview"),
  diagnostics: document.querySelector("#diagnostics-panel"),
  summary: document.querySelector("#summary-panel"),
  info: document.querySelector("#info-panel"),
  tabs: [...document.querySelectorAll(".tab")],
  panels: [...document.querySelectorAll(".panel")],
};

window.addEventListener("pywebviewready", init);

async function init() {
  bindEvents();
  const profiles = await window.pywebview.api.get_profiles();
  if (profiles.ok) {
    els.profile.innerHTML = profiles.profiles
      .map((profile) => `<option value="${escapeAttr(profile.name)}">${escapeHtml(profile.name)}</option>`)
      .join("");
    els.profile.value = state.profile;
  }
  renderDiagnostics([]);
  renderSummary({});
  renderInfo();
}

function bindEvents() {
  els.openFile.addEventListener("click", openFile);
  els.render.addEventListener("click", renderCurrent);
  els.inspect.addEventListener("click", inspectCurrent);
  els.openExternal.addEventListener("click", () => window.pywebview.api.open_external_html());
  els.reload.addEventListener("click", renderCurrent);
  els.profile.addEventListener("change", () => {
    state.profile = els.profile.value;
  });
  els.tabs.forEach((tab) => {
    tab.addEventListener("click", () => activateTab(tab.dataset.tab));
  });
}

async function openFile() {
  const result = await window.pywebview.api.open_file_dialog();
  if (result.ok) {
    state.filePath = result.file_path;
    updateCurrentFile();
    await inspectCurrent();
  }
}

async function renderCurrent() {
  const payload = await window.pywebview.api.render_current(state.filePath, els.profile.value || state.profile);
  handlePayload(payload);
  if (payload.ok && payload.html_url) {
    state.htmlPath = payload.html_path;
    state.htmlUrl = payload.html_url;
    els.preview.src = payload.html_url;
    els.preview.classList.add("active");
    els.emptyPreview.classList.add("hidden");
    activateTab("diagnostics");
  }
}

async function inspectCurrent() {
  const payload = await window.pywebview.api.inspect_current(state.filePath);
  handlePayload(payload);
  activateTab("summary");
}

function handlePayload(payload) {
  state.lastPayload = payload;
  if (payload.file_path) {
    state.filePath = payload.file_path;
  }
  if (payload.profile && payload.profile !== "-") {
    state.profile = payload.profile;
  }
  updateCurrentFile();
  renderDiagnostics(payload.diagnostics || []);
  renderSummary(payload.summary || {}, payload.diagnostics || []);
  renderInfo(payload);
}

function updateCurrentFile() {
  els.currentFile.textContent = state.filePath || "Aucun fichier sélectionné";
  els.currentFile.title = state.filePath || "";
}

function activateTab(name) {
  els.tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === name));
  els.panels.forEach((panel) => panel.classList.toggle("active", panel.id === `${name}-panel`));
}

function renderDiagnostics(diagnostics) {
  if (!diagnostics.length) {
    els.diagnostics.innerHTML = "<p>Aucun diagnostic.</p>";
    return;
  }
  els.diagnostics.innerHTML = diagnostics.map((diag) => `
    <article class="diagnostic ${escapeAttr(diag.level || "info")}">
      <div class="diagnostic-head">
        <span class="level">${escapeHtml(diag.level || "info")}</span>
        <span class="code">${escapeHtml(diag.code || "-")}</span>
      </div>
      <div>${escapeHtml(diag.message || "")}</div>
      ${detailsBlock(diag.details)}
    </article>
  `).join("");
}

function renderSummary(summary, diagnostics = []) {
  const counts = summary.counts || {};
  const unhandled = summary.unhandled_elements || [];
  const brokenRefs = detailList(diagnostics, "broken-local-ref", "refs");
  const missingMedia = detailList(diagnostics, "missing-media", "media");
  els.summary.innerHTML = `
    <dl class="summary-grid">
      <dt>Profil suggéré</dt><dd>${escapeHtml(summary.suggested_profile || "-")}</dd>
      <dt>Raison</dt><dd>${escapeHtml(summary.suggestion_reason || "-")}</dd>
      <dt>Éléments TEI distincts</dt><dd>${escapeHtml(summary.distinct_tei_elements ?? "-")}</dd>
      <dt>Éléments non traités</dt><dd>${escapeHtml(summary.unhandled_occurrences ?? 0)}</dd>
      <dt>Notes</dt><dd>${escapeHtml(counts.note ?? 0)}</dd>
      <dt>Apparats</dt><dd>${escapeHtml(counts.app ?? 0)}</dd>
      <dt>pb</dt><dd>${escapeHtml(counts.pb ?? 0)}</dd>
      <dt>graphic</dt><dd>${escapeHtml(counts.graphic ?? 0)}</dd>
    </dl>
    <h3>Éléments non traités</h3>
    ${listBlock(unhandled)}
    <h3>Références cassées</h3>
    ${listBlock(brokenRefs)}
    <h3>Médias manquants</h3>
    ${listBlock(missingMedia)}
    <h3>Résumé brut</h3>
    <pre>${escapeHtml(JSON.stringify(summary, null, 2))}</pre>
  `;
}

function renderInfo(payload = state.lastPayload || {}) {
  els.info.innerHTML = `
    <dl class="summary-grid">
      <dt>Fichier TEI</dt><dd>${escapeHtml(state.filePath || "-")}</dd>
      <dt>HTML</dt><dd>${escapeHtml(payload.html_path || state.htmlPath || "-")}</dd>
      <dt>Profil</dt><dd>${escapeHtml(payload.profile || state.profile || "-")}</dd>
      <dt>État</dt><dd>${payload.ok ? "OK" : "—"}</dd>
    </dl>
  `;
}

function detailsBlock(details) {
  if (!details || !Object.keys(details).length) {
    return "";
  }
  return `<pre>${escapeHtml(JSON.stringify(details, null, 2))}</pre>`;
}

function listBlock(items) {
  if (!items.length) {
    return "<p>—</p>";
  }
  return `<ul class="list">${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function detailList(diagnostics, code, key) {
  const found = diagnostics.find((diag) => diag.code === code);
  const values = found && found.details ? found.details[key] : [];
  return Array.isArray(values) ? values : [];
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("'", "&#39;");
}
