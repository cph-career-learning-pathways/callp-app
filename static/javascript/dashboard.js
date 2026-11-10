/* Student dashboard mock UI. No API calls or persistent writes. */
(() => {
  "use strict";
  const app = document.getElementById("dashboard-app");
  if (!app) return;

  // These demonstration records are deliberately separate from Django/RDS data.
  const data = {
    streak: 6,
    collections: [
      { id: 1, title: "Interview Prep", description: "Preparing for technical and behavioral interviews", count: 6, visibility: "private" },
      { id: 2, title: "Web Development", description: "Frontend and backend development fundamentals", count: 4, visibility: "unlisted" },
      { id: 3, title: "AI & Data Science", description: "Machine learning and analytics", count: 5, visibility: "public" },
    ],
    saved: [
      { id: "s1", type: "course", title: "Machine Learning Foundations", description: "Explore models and real-world applications." },
      { id: "s2", type: "article", title: "Git & Version Control Basics", description: "Track and collaborate on code." },
      { id: "s3", type: "article", title: "System Design Interview Guide", description: "Design scalable systems with confidence." },
    ],
    collectionRecommendations: [
      { id: "c1", type: "article", title: "System Design Interview Guide", description: "A practical preparation guide." },
      { id: "c2", type: "course", title: "Open Source Contribution Workshop", description: "Make your first community contribution." },
      { id: "c3", type: "course", title: "Machine Learning Foundations", description: "Learn introductory machine learning." },
    ],
    savedRecommendations: [
      { id: "r1", type: "article", title: "Operating Systems Reader", description: "Learn processes, memory, and storage." },
      { id: "r2", type: "course", title: "Cybersecurity Essentials", description: "Security foundations and good practices." },
      { id: "r3", type: "course", title: "Cloud Fundamentals Certificate", description: "Understand core cloud services." },
    ],
    viewed: [
      { id: "v1", type: "course", title: "Data Structures Practice Set", when: "Nov 02", description: "Arrays, trees and graphs." },
      { id: "v2", type: "course", title: "Intro to SQL Databases", when: "Nov 02", description: "Query and model relational data." },
      { id: "v3", type: "course", title: "Cloud Computing Essentials", when: "Nov 01", description: "Cloud concepts and services." },
    ],
    progress: [
      { id: "p1", type: "course", title: "Data Structures Practice Set", description: "Hands-on problems covering arrays, trees and graphs.", reward: 200, percent: 50, lastOpened: "Mon Nov 02" },
      { id: "p2", type: "course", title: "Intro to SQL Databases", description: "Query, join, and model relational data.", reward: 150, percent: 25, lastOpened: "Mon Nov 02" },
      { id: "p3", type: "course", title: "Cloud Computing Essentials", description: "Core cloud concepts and services for entry-level roles.", reward: 300, percent: 0, lastOpened: "Sun Nov 01" },
    ],
    pathways: [
      { id: 1, title: "Data Analytics Fundamentals", description: "A practical introduction to data skills", progress: 60, steps: 5 },
      { id: 2, title: "Career Readiness", description: "Prepare for internships and interviews", progress: 25, steps: 4 },
    ],
  };

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const escapeHTML = value => String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const folderIcon = '<svg class="dashboard-folder" viewBox="0 0 28 28" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M2 7a3 3 0 0 1 3-3h6l3 3h9a3 3 0 0 1 3 3v13H2z"/></svg>';
  let toastTimeout;

  function toast(message) {
    const element = $("#dashboard-toast");
    element.textContent = message;
    element.hidden = false;
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => { element.hidden = true; }, 3500);
  }

  function insertHeaderStreak() {
    const topbar = $(".student-dashboard-page .topbar");
    if (!topbar || $(".dashboard-header-streak")) return;
    const element = document.createElement("div");
    element.className = "dashboard-header-streak";
    element.innerHTML = `<span class="dashboard-fire" aria-hidden="true">🔥</span><span>${data.streak} Day Streak</span>`;
    const account = $(".account-dropdown", topbar);
    if (account) topbar.insertBefore(element, account);
    else topbar.append(element);
  }

  function collectionCard(collection) {
    return `<article class="dashboard-collection-tile">
      ${folderIcon}
      <div class="dashboard-collection-top"><span class="dashboard-visibility">${escapeHTML(collection.visibility)}</span></div>
      <h3>${escapeHTML(collection.title)}</h3><p>${Number(collection.count)} resources</p>
      <div class="dashboard-tile-actions"><button type="button" class="dashboard-tile-action" data-collection-open="${collection.id}">Details</button><button type="button" class="dashboard-tile-action" data-collection-share="${collection.id}">Share</button></div>
    </article>`;
  }

  function resourceCard(resource, options = {}) {
    const saved = data.saved.some(item => item.title === resource.title);
    const action = options.allowSave
      ? `<button type="button" class="dashboard-mini-button" data-toggle-save="${escapeHTML(resource.id)}" data-source="${escapeHTML(options.source)}">${saved ? 'Saved ✓' : '+ Save'}</button>`
      : "";
    const last = resource.when ? `<span>Opened ${escapeHTML(resource.when)}</span>` : "";
    return `<article class="dashboard-resource-tile"><span class="dashboard-resource-type">${escapeHTML(resource.type)}</span>
      <h3>${escapeHTML(resource.title)}</h3><p>${escapeHTML(resource.description || "")}</p>
      <div class="dashboard-resource-bottom">${last || '<span>Explore resources</span>'}${action}</div></article>`;
  }

  function renderCollections() {
    $("#dashboard-collections").innerHTML = data.collections.length ? data.collections.map(collectionCard).join("") : '<div class="dashboard-empty">You haven’t created a collection yet.</div>';
    $("#dashboard-collection-recommendations").innerHTML = data.collectionRecommendations.map(r => resourceCard(r, { allowSave: true, source: "collectionRecommendations" })).join("");
  }
  function renderSaved() {
    $("#saved-count").textContent = `${data.saved.length} saved`;
    $("#dashboard-saved").innerHTML = data.saved.length ? data.saved.map(r => resourceCard(r, { allowSave: true, source: "saved" })).join("") : '<div class="dashboard-empty">No saved resources yet.</div>';
    $("#dashboard-saved-recommendations").innerHTML = data.savedRecommendations.map(r => resourceCard(r, { allowSave: true, source: "savedRecommendations" })).join("");
  }
  function renderViewed() {
    $("#dashboard-viewed").innerHTML = data.viewed.length ? data.viewed.map(resourceCard).join("") : '<div class="dashboard-empty">You haven’t opened any resources yet.</div>';
  }
  function renderProgress() {
    $("#progress-count").textContent = `${data.progress.filter(p => p.percent === 100).length} completed`;
    $("#dashboard-progress").innerHTML = data.progress.map(resource => `<article class="dashboard-progress-card">
      <div class="dashboard-progress-identity"><span class="dashboard-resource-type">${escapeHTML(resource.type)}</span><h3>${escapeHTML(resource.title)}</h3></div>
      <div class="dashboard-progress-detail"><p>${escapeHTML(resource.description)} <strong>${resource.reward} XP</strong> awarded upon completion.</p>
        <div class="dashboard-progress-meta"><span>Last Opened: ${escapeHTML(resource.lastOpened)}</span><span>${resource.percent}% Complete</span></div>
        <div class="dashboard-progress-track" role="progressbar" aria-label="${escapeHTML(resource.title)} progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${resource.percent}"><span style="width:${resource.percent}%"></span></div>
        <div class="dashboard-progress-controls"><button type="button" class="dashboard-action dashboard-action-primary" data-progress="${resource.id}" ${resource.percent === 100 ? 'disabled' : ''}>${resource.percent === 100 ? '✓ Completed' : '+ Log 25% progress'}</button></div>
      </div></article>`).join("");
    $("#dashboard-pathways").innerHTML = data.pathways.map(p => `<article class="dashboard-pathway-card"><h3>${escapeHTML(p.title)}</h3><p>${escapeHTML(p.description)}</p><div class="dashboard-pathway-meta"><span>${p.steps} resources</span><strong>${p.progress}% complete</strong></div><div class="dashboard-pathway-track" role="progressbar" aria-label="${escapeHTML(p.title)} pathway progress" aria-valuenow="${p.progress}" aria-valuemin="0" aria-valuemax="100"><span style="width:${p.progress}%"></span></div></article>`).join("");
  }

  const tabRenders = { collections: renderCollections, saved: renderSaved, viewed: renderViewed, progress: renderProgress };
  const loaded = new Set();
  function showTab(tab, shouldFocus = false) {
    if (!tabRenders[tab]) return;
    // Only render a section the first time it is visited (lazy local-data rendering).
    if (!loaded.has(tab)) { tabRenders[tab](); loaded.add(tab); }
    $$("[data-tab]").forEach(button => {
      const isActive = button.dataset.tab === tab;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-selected", String(isActive));
      button.tabIndex = isActive ? 0 : -1;
      if (isActive && shouldFocus) button.focus();
    });
    $$(".dash-panel").forEach(panel => { panel.hidden = panel.id !== `dash-panel-${tab}`; });
    if (window.history.replaceState) history.replaceState(null, "", `#${tab}`);
  }

  $$("[data-tab]").forEach(button => {
    button.addEventListener("click", () => showTab(button.dataset.tab));
    button.addEventListener("keydown", e => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key)) return;
      e.preventDefault();
      const tabs = $$("[data-tab]");
      const current = tabs.indexOf(button);
      const index = e.key === "Home" ? 0 : e.key === "End" ? tabs.length - 1 : (current + (e.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
      showTab(tabs[index].dataset.tab, true);
    });
  });
  $$("[data-show-tab]").forEach(button => button.addEventListener("click", () => showTab(button.dataset.showTab)));
  window.addEventListener("hashchange", () => { const name = location.hash.slice(1); if (tabRenders[name]) showTab(name); });

  $("#dashboard-content").addEventListener("click", event => {
    const log = event.target.closest("[data-progress]");
    if (log) {
      const record = data.progress.find(r => r.id === log.dataset.progress);
      if (!record) return;
      record.percent = Math.min(100, record.percent + 25);
      renderProgress();
      toast(record.percent === 100 ? "Resource completed in mock data!" : `Progress updated to ${record.percent}% (mock only).`);
      return;
    }
    const save = event.target.closest("[data-toggle-save]");
    if (save) {
      const source = data[save.dataset.source];
      const record = source?.find(r => String(r.id) === save.dataset.toggleSave);
      if (!record) return;
      const oldIndex = data.saved.findIndex(r => r.title === record.title);
      if (oldIndex >= 0) { data.saved.splice(oldIndex, 1); toast("Removed from mock saved resources."); }
      else { data.saved.unshift({ ...record }); toast("Added to mock saved resources."); }
      loaded.delete("saved");
      if (!$("#dash-panel-saved").hidden) { renderSaved(); loaded.add("saved"); }
      if (!$("#dash-panel-collections").hidden) renderCollections();
      return;
    }
    const share = event.target.closest("[data-collection-share]");
    if (share) {
      const c = data.collections.find(r => String(r.id) === share.dataset.collectionShare);
      if (c) toast(`“${c.title}” is ${c.visibility}. Real share links will be enabled after backend integration.`);
      return;
    }
    const details = event.target.closest("[data-collection-open]");
    if (details) {
      const c = data.collections.find(r => String(r.id) === details.dataset.collectionOpen);
      if (c) toast(`${c.title}: ${c.count} sample resources. Collection detail view is not connected yet.`);
    }
  });

  const dialog = $("#collection-dialog");
  $("#new-collection-button").addEventListener("click", () => dialog.showModal());
  $$("[data-close-dialog]").forEach(button => button.addEventListener("click", () => dialog.close()));
  dialog.addEventListener("click", e => { if (e.target === dialog) dialog.close(); });
  $("#collection-form").addEventListener("submit", event => {
    event.preventDefault();
    const form = event.currentTarget;
    const title = form.elements.title.value.trim();
    if (!title) return;
    data.collections.unshift({ id: Date.now(), title, description: form.elements.description.value.trim(), visibility: form.elements.visibility.value, count: 0 });
    renderCollections(); loaded.add("collections");
    dialog.close(); form.reset();
    toast("Mock collection created. Reloading resets demo changes.");
  });

  insertHeaderStreak();
  const initial = location.hash.slice(1);
  showTab(tabRenders[initial] ? initial : "collections");
})();
