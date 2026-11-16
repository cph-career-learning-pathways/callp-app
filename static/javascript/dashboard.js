/* Student dashboard: server-provided data and persistent Django API actions. */
(() => {
  "use strict";
  const app = document.getElementById("dashboard-app");
  const stateNode = document.getElementById("dashboard-data");
  if (!app || !stateNode) return;
  const data = JSON.parse(stateNode.textContent);
  const apiUrl = app.dataset.apiUrl;
  const csrf = document.querySelector('#collection-form [name="csrfmiddlewaretoken"]')?.value;
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => Array.from(root.querySelectorAll(s));
  const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const validUrl = v => { try {const u = new URL(v); return ["http:","https:"].includes(u.protocol) ? u.href : "";} catch {return "";} };
  const folder = '<svg class="dashboard-folder" viewBox="0 0 28 28" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M2 7a3 3 0 0 1 3-3h6l3 3h9a3 3 0 0 1 3 3v13H2z"/></svg>';
  let toastTimer;
  const toast = message => { const el = $("#dashboard-toast"); el.textContent = message; el.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => el.hidden = true, 3500); };
  async function send(action, props = {}) {
    const response = await fetch(apiUrl, {
      method: "POST", credentials: "same-origin",
      headers: {"Content-Type": "application/json", "X-CSRFToken": csrf},
      body: JSON.stringify({action, ...props}),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.error || `Request failed (${response.status}).`);
    return result;
  }
  function streakHeader() {
    const bar = $(".student-dashboard-page .topbar");
    if (!bar || $(".dashboard-header-streak")) return;
    const el = document.createElement("div");
    el.className = "dashboard-header-streak";
    el.innerHTML = `<span class="dashboard-fire" aria-hidden="true">🔥</span><span>${Number(data.streak || 0)} Day Streak</span>`;
    bar.insertBefore(el, $(".account-dropdown", bar) || null);
  }
  function card(r, allowSave = false) {
    const href = validUrl(r.url);
    const name = href ? `<a href="${esc(href)}" target="_blank" rel="noopener noreferrer" data-visit="${esc(r.id)}">${esc(r.title)}</a>` : esc(r.title);
    const saved = data.saved.some(item => item.id === r.id);
    return `<article class="dashboard-resource-tile"><span class="dashboard-resource-type">${esc(r.type)}</span>
      <h3>${name}</h3><p>${esc(r.description)}</p><div class="dashboard-resource-bottom">
      <span>${r.when ? `Opened ${esc(r.when)}` : ""}</span>
      ${allowSave ? `<button type="button" class="dashboard-mini-button" data-toggle-save="${esc(r.id)}">${saved ? "Saved ✓" : "+ Save"}</button>` : ""}</div></article>`;
  }
  function renderCollections() {
    $("#dashboard-collections").innerHTML = data.collections.length ? data.collections.map(c => `<article class="dashboard-collection-tile">
      ${folder}<div class="dashboard-collection-top"><span class="dashboard-visibility">${esc(c.visibility)}</span></div>
      <h3>${esc(c.title)}</h3><p>${Number(c.count)} resources</p>
      <div class="dashboard-tile-actions"><button type="button" class="dashboard-tile-action" data-collection-open="${esc(c.id)}">Details</button></div></article>`).join("")
      : '<div class="dashboard-empty">You haven’t created a collection yet.</div>';
    renderResourceList("#dashboard-collection-recommendations", data.collectionRecommendations, true, "No matching recommendations yet.");
  }
  function renderResourceList(selector, values, allowSave, empty) {
    $(selector).innerHTML = values.length ? values.map(r => card(r, allowSave)).join("") : `<div class="dashboard-empty">${esc(empty)}</div>`;
  }
  function renderSaved() {
    $("#saved-count").textContent = `${data.saved.length} saved`;
    renderResourceList("#dashboard-saved", data.saved, true, "No saved resources yet.");
    renderResourceList("#dashboard-saved-recommendations", data.savedRecommendations, true, "No matching recommendations yet.");
  }
  function renderViewed() { renderResourceList("#dashboard-viewed", data.viewed, false, "You haven’t opened any resources yet."); }
  function renderProgress() {
    $("#progress-count").textContent = `${data.progress.filter(p => p.percent === 100).length} completed`;
    $("#dashboard-progress").innerHTML = data.progress.length ? data.progress.map(r => {
      const percent = Math.max(0, Math.min(100, Number(r.percent) || 0));
      const href = validUrl(r.url);
      return `<article class="dashboard-progress-card"><div class="dashboard-progress-identity">
        <span class="dashboard-resource-type">${esc(r.type)}</span><h3>${href ? `<a href="${esc(href)}" target="_blank" rel="noopener noreferrer" data-visit="${esc(r.id)}">${esc(r.title)}</a>` : esc(r.title)}</h3></div>
        <div class="dashboard-progress-detail"><p>${esc(r.description)} ${Number(r.reward) ? `<strong>${Number(r.reward)} XP</strong> on completion.` : ""}</p>
        <div class="dashboard-progress-meta"><span>${r.lastOpened ? `Last Opened: ${esc(r.lastOpened)}` : "Not opened yet"}</span><span>${percent}% Complete</span></div>
        <div class="dashboard-progress-track" role="progressbar" aria-label="${esc(r.title)} progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${percent}"><span style="width:${percent}%"></span></div>
        <div class="dashboard-progress-controls"><button type="button" class="dashboard-action dashboard-action-primary" data-progress="${esc(r.id)}" ${percent === 100 ? "disabled" : ""}>${percent === 100 ? "✓ Completed" : "+ Log 25% progress"}</button></div></div></article>`;
    }).join("") : '<div class="dashboard-empty">No resource progress yet.</div>';
    $("#dashboard-pathways").innerHTML = data.pathways.length ? data.pathways.map(p => {
      const percent = Math.max(0, Math.min(100, Number(p.progress) || 0));
      return `<article class="dashboard-pathway-card"><h3>${esc(p.title)}</h3><p>${esc(p.description)}</p>
        <div class="dashboard-pathway-meta"><span>${Number(p.steps)} resources</span><strong>${percent}% complete</strong></div>
        <div class="dashboard-pathway-track" role="progressbar" aria-label="${esc(p.title)} pathway progress" aria-valuenow="${percent}" aria-valuemin="0" aria-valuemax="100"><span style="width:${percent}%"></span></div></article>`;
    }).join("") : '<div class="dashboard-empty">No learning pathways started yet.</div>';
  }
  function showTab(tab, focus = false) {
    // Only the four supported dashboard tabs can trigger a renderer.
    switch (tab) {
      case "collections":
        renderCollections();
        break;
      case "saved":
        renderSaved();
        break;
      case "viewed":
        renderViewed();
        break;
      case "progress":
        renderProgress();
        break;
      default:
        return false;
    }
    $$('[data-tab]').forEach(b => {const active = b.dataset.tab === tab; b.classList.toggle("is-active", active); b.setAttribute("aria-selected", String(active)); b.tabIndex = active ? 0 : -1; if (active && focus) b.focus();});
    $$(".dash-panel").forEach(p => p.hidden = p.id !== `dash-panel-${tab}`);
    history.replaceState(null, "", `#${tab}`);
    return true;
  }
  $$('[data-tab]').forEach(button => {
    button.addEventListener("click", () => showTab(button.dataset.tab));
    button.addEventListener("keydown", e => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key)) return;
      e.preventDefault(); const tabs = $$('[data-tab]'); const i = tabs.indexOf(button);
      const next = e.key === "Home" ? 0 : e.key === "End" ? tabs.length - 1 : (i + (e.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
      showTab(tabs[next].dataset.tab, true);
    });
  });
  $$('[data-show-tab]').forEach(b => b.addEventListener("click", () => showTab(b.dataset.showTab)));
  window.addEventListener("hashchange", () => showTab(location.hash.slice(1)));
  $("#dashboard-content").addEventListener("click", async event => {
    const link = event.target.closest('[data-visit]');
    if (link) { send("visit", {resource_id: link.dataset.visit}).catch(console.error); return; }
    const button = event.target.closest('[data-progress], [data-toggle-save], [data-collection-open]');
    if (!button) return;
    const detail = button.dataset.collectionOpen;
    if (detail) {
      const c = data.collections.find(x => x.id === detail);
      if (!c) return;
      const resources = c.resources || [];
      const container = $("#collection-details-content");
      $("#collection-details-title").textContent = c.title;
      container.replaceChildren();
      if (!resources.length) container.textContent = "There are no resources in this collection yet.";
      resources.forEach(r => {
        const p = document.createElement("p"); const a = document.createElement("a");
        a.textContent = r.title; a.href = validUrl(r.url) || "#"; a.target = "_blank"; a.rel = "noopener noreferrer";
        a.addEventListener("click", () => send("visit", {resource_id: r.id}).catch(console.error));
        p.append(a); container.append(p);
      });
      $("#collection-details-dialog").showModal(); return;
    }
    button.disabled = true;
    try {
      if (button.dataset.progress) {
        const result = await send("increment_progress", {resource_id: button.dataset.progress});
        const r = data.progress.find(x => x.id === button.dataset.progress);
        if (r) r.percent = result.percent;
        renderProgress(); toast(result.awarded_xp ? `Progress saved. Earned ${result.awarded_xp} XP!` : "Progress saved.");
      } else if (button.dataset.toggleSave) {
        const id = button.dataset.toggleSave;
        const result = await send("toggle_save", {resource_id: id});
        if (result.saved) {
          const record = [...data.savedRecommendations, ...data.collectionRecommendations, ...data.saved, ...data.viewed].find(r => r.id === id);
          if (record) data.saved.unshift(record);
        } else data.saved = data.saved.filter(r => r.id !== id);
        renderSaved(); renderCollections(); toast(result.saved ? "Resource saved." : "Resource removed from saved.");
      }
    } catch (error) { toast(error.message); }
    finally {button.disabled = false;}
  });
  const dialog = $("#collection-dialog");
  $("#new-collection-button").addEventListener("click", () => dialog.showModal());
  $$('[data-close-dialog]').forEach(b => b.addEventListener("click", () => b.closest("dialog").close()));
  $$('dialog').forEach(d => d.addEventListener("click", e => {if (e.target === d) d.close();}));
  $("#collection-form").addEventListener("submit", async event => {
    event.preventDefault(); const form = event.currentTarget; const submit = form.querySelector('[type="submit"]');
    submit.disabled = true;
    try {
      await send("create_collection", {title: form.elements.title.value.trim(), description: form.elements.description.value.trim(), visibility: form.elements.visibility.value});
      location.hash = "collections"; location.reload();
    } catch (error) { toast(error.message); submit.disabled = false; }
  });
  streakHeader();
  if (!showTab(location.hash.slice(1))) showTab("collections");
})();


