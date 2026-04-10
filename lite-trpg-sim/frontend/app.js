/**
 * Frontend controller for the local story-engine UI.
 *
 * This file intentionally stays story-agnostic: it renders the generic view
 * returned by the backend and keeps browser-local save slot management.
 */
const API_BASE = "http://127.0.0.1:8787";
const SAVE_STORE_KEY = "lite_trpg_sim_save_store_v2";
const ACTIVE_SLOT_KEY = "lite_trpg_sim_active_slot_v2";
const FRONTEND_DEBUG_KEY = "lite_trpg_sim_frontend_debug_v1";
const SLOT_IDS = ["1", "2", "3", "4", "5"];

let meta = null;
let currentView = null;
let currentStoryId = null;
let saveStore = loadSaveStore();

const els = {
  title: document.getElementById("game-title"),
  chapter: document.getElementById("chapter-title"),
  sceneTitle: document.getElementById("scene-title"),
  sceneMeta: document.getElementById("scene-meta"),
  sceneText: document.getElementById("scene-text"),
  actions: document.getElementById("actions"),
  runtimeStatus: document.getElementById("runtime-status"),
  outcomeContent: document.getElementById("outcome-content"),
  encounterBox: document.getElementById("encounter-box"),
  encounterContent: document.getElementById("encounter-content"),
  playerSummary: document.getElementById("player-summary"),
  statsGrid: document.getElementById("stats-grid"),
  skillGrid: document.getElementById("skill-grid"),
  resourceGrid: document.getElementById("resource-grid"),
  statusList: document.getElementById("status-list"),
  inventoryList: document.getElementById("inventory-list"),
  logList: document.getElementById("log-list"),
  saveBtn: document.getElementById("save-btn"),
  loadBtn: document.getElementById("load-btn"),
  exportBtn: document.getElementById("export-btn"),
  importBtn: document.getElementById("import-btn"),
  importInput: document.getElementById("import-input"),
  restartBtn: document.getElementById("restart-btn"),
  slotSelect: document.getElementById("slot-select"),
  slotStatus: document.getElementById("slot-status"),
  overlay: document.getElementById("setup-overlay"),
  worldIntro: document.getElementById("world-intro"),
  storySetupSummary: document.getElementById("story-setup-summary"),
  storySetupDetails: document.getElementById("story-setup-details"),
  storySelect: document.getElementById("story-select"),
  nameInput: document.getElementById("name-input"),
  professionSelect: document.getElementById("profession-select"),
  professionPreview: document.getElementById("profession-preview"),
  newGameBtn: document.getElementById("new-game-btn"),
  continueBtn: document.getElementById("continue-btn"),
  setupStatus: document.getElementById("setup-status"),
};

/** Persist a small rolling frontend debug buffer for later bug reports. */
function pushFrontendDebug(label, payload = {}) {
  const entry = {
    label,
    payload,
    timestamp: new Date().toISOString(),
  };
  let buffer = [];
  try {
    const raw = localStorage.getItem(FRONTEND_DEBUG_KEY);
    buffer = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(buffer)) {
      buffer = [];
    }
  } catch {
    buffer = [];
  }

  buffer.push(entry);
  buffer = buffer.slice(-30);
  try {
    localStorage.setItem(FRONTEND_DEBUG_KEY, JSON.stringify(buffer));
  } catch {
    // Debug buffering must stay best-effort and never block play.
  }
  console.info(`[LiteTRPGSim] ${label}`, payload);
}

/** Render setup-screen status text without throwing alerts. */
function setSetupStatus(message, isError = false) {
  els.setupStatus.textContent = message || "";
  els.setupStatus.style.color = isError ? "#efb7a7" : "#b7d6be";
}

/** Render compact toolbar feedback for slot/save/import/export operations. */
function setSlotStatusMessage(message, tone = "neutral") {
  els.slotStatus.textContent = message || "";
  els.slotStatus.dataset.tone = tone;
}

/** Render non-modal runtime feedback near the action list. */
function setRuntimeStatusMessage(message, tone = "neutral") {
  const text = String(message || "").trim();
  els.runtimeStatus.hidden = !text;
  els.runtimeStatus.textContent = text;
  els.runtimeStatus.dataset.tone = tone;
}

/** Render one labeled line used by outcome and encounter summary sections. */
function renderInfoLine(label, content) {
  return `<div class="info-line"><span class="info-label">${escapeHtml(label)}</span><span>${content}</span></div>`;
}

/** Render one compact information section used by outcome and encounter panels. */
function renderInfoSection(title, rows) {
  const validRows = rows.filter(Boolean).join("");
  if (!validRows) {
    return "";
  }
  return `<div class="info-section"><div class="info-section-title">${escapeHtml(title)}</div>${validRows}</div>`;
}

/** Enable or disable the top toolbar based on whether a run is active. */
function setToolbarEnabled(enabled) {
  els.saveBtn.disabled = !enabled;
  els.exportBtn.disabled = false;
  els.restartBtn.disabled = !enabled;
  els.loadBtn.disabled = false;
  els.importBtn.disabled = false;
  els.slotSelect.disabled = false;
}

/** Load browser-local save slots and autosave metadata. */
function loadSaveStore() {
  const fallback = { version: 2, slots: {}, autosave: null };
  const raw = localStorage.getItem(SAVE_STORE_KEY);
  if (!raw) {
    return fallback;
  }
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") {
      return fallback;
    }
    return {
      version: 2,
      slots: parsed.slots && typeof parsed.slots === "object" ? parsed.slots : {},
      autosave: parsed.autosave && typeof parsed.autosave === "object" ? parsed.autosave : null,
    };
  } catch {
    return fallback;
  }
}

/** Persist the current local save-slot structure. */
function persistSaveStore() {
  localStorage.setItem(SAVE_STORE_KEY, JSON.stringify(saveStore));
}

/** Return the currently selected slot id, defaulting to slot 1. */
function getActiveSlotId() {
  const cached = localStorage.getItem(ACTIVE_SLOT_KEY);
  if (cached && SLOT_IDS.includes(cached)) {
    return cached;
  }
  return SLOT_IDS[0];
}

/** Persist the active slot selection for later visits. */
function setActiveSlotId(slotId) {
  if (!SLOT_IDS.includes(slotId)) {
    return;
  }
  localStorage.setItem(ACTIVE_SLOT_KEY, slotId);
}

/** Format backend timestamps for the local Chinese UI. */
function formatTime(isoText) {
  if (!isoText) {
    return "未知时间";
  }
  const date = new Date(isoText);
  if (Number.isNaN(date.getTime())) {
    return "未知时间";
  }
  return date.toLocaleString("zh-CN", { hour12: false });
}

/** Return one slot entry from the local store. */
function slotEntry(slotId) {
  return saveStore.slots?.[slotId] || null;
}

/** Return whether any autosave or manual save exists locally. */
function hasAnySaveEntry() {
  return Boolean(saveStore.autosave) || SLOT_IDS.some((slotId) => Boolean(slotEntry(slotId)));
}

/** Rebuild the slot-select options from the current local store. */
function refreshSlotOptions() {
  const activeSlotId = getActiveSlotId();
  const optionHtml = SLOT_IDS.map((slotId) => {
    const entry = slotEntry(slotId);
    const suffix = entry ? ` · ${formatTime(entry.saved_at)}` : " · 空";
    return `<option value="${slotId}">槽位 ${slotId}${suffix}</option>`;
  }).join("");
  els.slotSelect.innerHTML = optionHtml;
  els.slotSelect.value = SLOT_IDS.includes(activeSlotId) ? activeSlotId : SLOT_IDS[0];
}

/** Refresh the small status label next to the selected slot. */
function refreshSlotStatus() {
  const selectedSlot = els.slotSelect.value || getActiveSlotId();
  const entry = slotEntry(selectedSlot);
  if (!entry) {
    setSlotStatusMessage(`槽位 ${selectedSlot}：空`, "neutral");
    return;
  }
  const parts = [
    `槽位 ${selectedSlot}`,
    entry.player_name || "未知角色",
    `回合 ${entry.turns ?? 0}`,
    formatTime(entry.saved_at),
  ];
  setSlotStatusMessage(parts.join(" · "), "neutral");
}

/** Insert or update one manual/imported save slot entry. */
function upsertSlot(slotId, saveData, view, source = "manual") {
  if (!SLOT_IDS.includes(slotId)) {
    return;
  }
  saveStore.slots[slotId] = {
    slot_id: slotId,
    source,
    saved_at: saveData.saved_at || new Date().toISOString(),
    story_id: saveData.story_id || view?.story_id || "",
    world_id: saveData.world_id || view?.world?.id || "",
    world_title: view?.world?.title || "",
    chapter_title: view?.world?.chapter_title || "",
    player_name: view?.player?.name || "",
    profession_name: view?.player?.profession_name || "",
    turns: view?.progress?.turns ?? null,
    node_id: view?.progress?.node_id || "",
    save_data: saveData,
  };
  persistSaveStore();
  refreshSlotOptions();
  refreshSlotStatus();
}

/** Update the dedicated autosave entry after each successful action. */
function writeAutosave(saveData, view) {
  saveStore.autosave = {
    source: "auto",
    saved_at: saveData.saved_at || new Date().toISOString(),
    story_id: saveData.story_id || view?.story_id || "",
    world_id: saveData.world_id || view?.world?.id || "",
    player_name: view?.player?.name || "",
    profession_name: view?.player?.profession_name || "",
    turns: view?.progress?.turns ?? null,
    node_id: view?.progress?.node_id || "",
    save_data: saveData,
  };
  persistSaveStore();
}

/** Return the newest save between autosave and manual slots. */
function latestSaveEntry() {
  const candidates = [];
  if (saveStore.autosave?.save_data) {
    candidates.push({ ...saveStore.autosave, slot_id: "auto" });
  }
  for (const slotId of SLOT_IDS) {
    const entry = slotEntry(slotId);
    if (entry?.save_data) {
      candidates.push(entry);
    }
  }
  if (!candidates.length) {
    return null;
  }
  candidates.sort((a, b) => {
    const ta = new Date(a.saved_at || 0).getTime();
    const tb = new Date(b.saved_at || 0).getTime();
    return tb - ta;
  });
  return candidates[0];
}

/** Thin wrapper around the backend JSON API with normalized error handling. */
async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    throw new Error("后端返回了无效 JSON。");
  }

  if (!response.ok || !payload.ok) {
    const errorText = payload?.error || `HTTP ${response.status}`;
    throw new Error(errorText);
  }
  return payload.data;
}

/** Look up one profession in the currently loaded story metadata. */
function professionById(professionId) {
  if (!meta) {
    return null;
  }
  return meta.professions.find((entry) => entry.id === professionId) || null;
}

/** Look up one story brief from the loaded meta payload. */
function storyBriefById(storyId) {
  if (!meta || !Array.isArray(meta.stories)) {
    return null;
  }
  return meta.stories.find((entry) => entry.id === storyId) || null;
}

/** Resolve an item display name from setup metadata. */
function itemName(itemId) {
  return meta?.items?.[itemId]?.name || itemId;
}

/** Resolve one skill id into the current story's label. */
function skillLabel(skillId) {
  return meta?.skill_meta?.[skillId]?.label || skillId;
}

/** Resolve one resource id into a story-configured player-facing label. */
function resourceLabel(resourceId, fallback) {
  const labels = meta?.world?.ui?.resource_labels;
  if (labels && typeof labels === "object" && typeof labels[resourceId] === "string" && labels[resourceId].trim()) {
    return labels[resourceId].trim();
  }
  return fallback;
}

/** Render optional setup summary/details from the selected story pack. */
function renderStorySetupMeta() {
  const story = storyBriefById(currentStoryId || meta?.active_story_id || meta?.default_story_id || "");
  const setupSummary = story?.setup_summary || "";
  const setupDetails = Array.isArray(story?.setup_details) ? story.setup_details : [];

  els.storySetupSummary.hidden = !setupSummary;
  els.storySetupSummary.textContent = setupSummary;

  const detailHtml = setupDetails
    .filter((entry) => entry && entry.label && entry.value)
    .map(
      (entry) =>
        `<span class="setup-detail-chip">${escapeHtml(String(entry.label))}：${escapeHtml(String(entry.value))}</span>`
    )
    .join("");
  els.storySetupDetails.hidden = !detailHtml;
  els.storySetupDetails.innerHTML = detailHtml;
}

/** Populate the story selector with installed story packs. */
function renderStoryOptions() {
  if (!meta) {
    els.storySelect.innerHTML = "";
    return;
  }

  const stories = Array.isArray(meta.stories) ? meta.stories : [];
  const fallback = [
    {
      id: meta.active_story_id || meta.default_story_id || "default",
      title: meta.world?.title || "默认故事",
      chapter_title: meta.world?.chapter_title || "",
    },
  ];
  const list = stories.length ? stories : fallback;

  els.storySelect.innerHTML = list
    .map((story) => {
      const chapter = story.chapter_title ? ` · ${story.chapter_title}` : "";
      return `<option value="${escapeHtml(story.id)}">${escapeHtml(story.title + chapter)}</option>`;
    })
    .join("");

  const preferred = currentStoryId || meta.active_story_id || meta.default_story_id || list[0].id;
  if (preferred) {
    els.storySelect.value = preferred;
  }
}

/** Populate the profession selector for the currently active story pack. */
function renderProfessionOptions() {
  const options = meta.professions
    .map((profession) => `<option value="${profession.id}">${profession.name}</option>`)
    .join("");
  els.professionSelect.innerHTML = options;
  renderProfessionPreview();
}

/** Convert a stats object into one human-readable summary line. */
function statLine(stats) {
  return Object.entries(stats)
    .map(([key, value]) => `${meta.stats[key]?.label || key} ${value}`)
    .join(" / ");
}

/** Convert a skills object into one concise preview line. */
function skillLine(skills) {
  const entries = Object.entries(skills || {}).filter(([, value]) => Number(value) > 0);
  if (!entries.length) {
    return "无";
  }
  return entries.map(([key, value]) => `${skillLabel(key)} ${value}`).join(" / ");
}

/** Render the selected profession preview block in the setup overlay. */
function renderProfessionPreview() {
  const profession = professionById(els.professionSelect.value);
  if (!profession) {
    els.professionPreview.textContent = "";
    return;
  }

  const perks = profession.perks.map((entry) => `• ${entry}`).join("\n");
  const itemNames = (profession.starting_items || []).map((itemId) => itemName(itemId)).join("、");
  els.professionPreview.textContent = [
    profession.summary,
    `\n属性：${statLine(profession.stats)}`,
    `\n技能：${skillLine(profession.skills)}`,
    `\n初始物品：${itemNames || "无"}`,
    `\n特性：\n${perks || "• 无"}`,
  ].join("\n");
}

/** Load meta for one story pack and update setup UI accordingly. */
async function loadMetaForStory(storyId) {
  const query = storyId ? `?story_id=${encodeURIComponent(storyId)}` : "";
  const nextMeta = await api(`/api/meta${query}`);
  meta = nextMeta;
  currentStoryId = meta.active_story_id || storyId || meta.default_story_id || null;

  renderStoryOptions();
  els.worldIntro.textContent = meta.world.intro || "";
  renderStorySetupMeta();
  renderProfessionOptions();

  if (!currentView) {
    els.title.textContent = meta.world.title;
    els.chapter.textContent = meta.world.chapter_title;
  }
}

/** Ensure local meta matches the currently rendered view's story id. */
async function syncMetaForView(view) {
  const storyId = view?.story_id;
  if (!storyId) {
    return;
  }
  if (meta?.active_story_id === storyId) {
    currentStoryId = storyId;
    const storyBrief = storyBriefById(storyId);
    if (storyBrief) {
      els.storySelect.value = storyId;
    }
    return;
  }
  await loadMetaForStory(storyId);
}

/** Render the last outcome block, including rolls and effect summaries. */
function renderOutcome(outcome) {
  if (!outcome) {
    els.outcomeContent.innerHTML = "尚无事件。";
    return;
  }

  const blocks = [];
  const resolution = outcome.resolution || null;
  blocks.push(
    renderInfoSection("摘要", [
      `<div class="outcome-summary">${escapeHtml(outcome.summary)}</div>`,
      outcome.detail ? `<div class="outcome-detail">${escapeHtml(outcome.detail || "")}</div>` : "",
    ])
  );

  if (outcome.roll) {
    const roll = outcome.roll;
    blocks.push(
      renderInfoSection("检定", [
        renderInfoLine("项目", escapeHtml(roll.label)),
        renderInfoLine(
          "结果",
          `d20=${roll.roll} + 修正${roll.modifier >= 0 ? "+" : ""}${roll.modifier} = ${roll.total} / DC ${roll.dc} (${roll.success ? "成功" : "失败"})`
        ),
      ])
    );

    if (Array.isArray(roll.breakdown) && roll.breakdown.length) {
      const entries = roll.breakdown
        .map((entry) => `<li>${escapeHtml(entry.source)} ${entry.value >= 0 ? "+" : ""}${entry.value}</li>`)
        .join("");
      blocks.push(`<ul class="breakdown-list">${entries}</ul>`);
    }
  } else if (resolution?.label) {
    const statusText =
      resolution.success === true ? "成功" : resolution.success === false ? "失败" : "完成";
    const explainSummary =
      typeof resolution?.explain?.summary === "string" ? resolution.explain.summary.trim() : "";
    const titleLine = explainSummary || `结算：${resolution.label} (${statusText})`;
    const resolutionRows = [renderInfoLine("结算", escapeHtml(titleLine))];

    if ((resolution.kind === "save" || resolution.kind === "check") && Number.isFinite(resolution.roll)) {
      const skillText = resolution.skill_label ? ` + ${escapeHtml(resolution.skill_label)}` : "";
      const statText = resolution.stat ? escapeHtml(meta?.stats?.[resolution.stat]?.label || resolution.stat) : "属性";
      resolutionRows.push(renderInfoLine("检定类型", `${statText}${skillText}`));
      resolutionRows.push(
        renderInfoLine(
          "结果",
          `d20=${resolution.roll} + 修正${resolution.modifier >= 0 ? "+" : ""}${resolution.modifier} = ${resolution.total} / DC ${resolution.dc}`
        )
      );
    }

    if (resolution.kind === "contest" && Number.isFinite(resolution.roll)) {
      if (resolution.stat) {
        const contestStat = escapeHtml(meta?.stats?.[resolution.stat]?.label || resolution.stat);
        const contestSkill = resolution.skill_label ? ` + ${escapeHtml(resolution.skill_label)}` : "";
        resolutionRows.push(renderInfoLine("对抗类型", `${contestStat}${contestSkill}`));
      }
      const opponentLabel = resolution.opponent_label || "对手";
      const playerLine = `你：d20=${resolution.roll} + 修正${resolution.modifier >= 0 ? "+" : ""}${resolution.modifier} = ${resolution.total}`;
      const opponentLine = `${escapeHtml(opponentLabel)}：d20=${resolution.opponent_roll} + 修正${resolution.opponent_modifier >= 0 ? "+" : ""}${resolution.opponent_modifier} = ${resolution.opponent_total}`;
      resolutionRows.push(renderInfoLine("你", playerLine));
      resolutionRows.push(renderInfoLine(opponentLabel, opponentLine));
      if (resolution.active_side) {
        const activeLabel = resolution.active_side === "player" ? "你" : escapeHtml(opponentLabel);
        resolutionRows.push(renderInfoLine("主动方", activeLabel));
      }
      if (resolution.tie === true) {
        resolutionRows.push(
          renderInfoLine(
            "平局判定",
            `${escapeHtml(resolution.tie_policy || "player_wins")} · 结果边际 ${Number(resolution.margin || 0)}`
          )
        );
      }
    }

    if (["damage", "healing", "drain"].includes(resolution.kind)) {
      const amount = Number(resolution.amount || 0);
      const mitigated = Number(resolution.mitigated || 0);
      const amplified = Number(resolution.amplified || 0);
      const shieldAbsorbed = Number(resolution.shield_absorbed || 0);
      const applied = Number(resolution.applied || 0);
      const shieldLabel = resourceLabel("shield", "护盾");
      const impactKind = resolution.impact_kind || resolution.kind || "damage";
      const damageType = resolution.damage_type || "physical";
      const targetLabel = resolution.target === "enemy" ? resolution.target_label || "敌方" : "你";
      const titleMap = { damage: "伤害", healing: "治疗", drain: "吸取" };
      resolutionRows.push(renderInfoLine("类型", escapeHtml(titleMap[impactKind] || "结算")));
      resolutionRows.push(renderInfoLine("伤害属性", escapeHtml(damageType)));
      resolutionRows.push(renderInfoLine("目标", escapeHtml(targetLabel)));
      resolutionRows.push(
        renderInfoLine(
          "影响",
          `宣告：${amount} · 减伤：${mitigated} · 易伤增幅：${amplified} · ${escapeHtml(shieldLabel)}吸收：${shieldAbsorbed} · 生效：${applied}`
        )
      );
      if (resolution.kind === "drain") {
        resolutionRows.push(renderInfoLine("吸取回复", String(Number(resolution.drain_recovered || 0))));
      }
    }
    blocks.push(renderInfoSection("结算明细", resolutionRows));

    if (Array.isArray(resolution.breakdown) && resolution.breakdown.length) {
      const entries = resolution.breakdown
        .map((entry) => `<li>${escapeHtml(entry.source)} ${entry.value >= 0 ? "+" : ""}${entry.value}</li>`)
        .join("");
      blocks.push(`<ul class="breakdown-list">${entries}</ul>`);
    }
  }

  if (Array.isArray(outcome.changes) && outcome.changes.length) {
    blocks.push(
      renderInfoSection(
        "变化",
        outcome.changes.map((entry) => `<div class="change-pill">${escapeHtml(entry)}</div>`)
      )
    );
  }

  els.outcomeContent.innerHTML = blocks.join("");
}

/** Render current player actions and surface availability from the backend view. */
function renderActions(view) {
  els.actions.innerHTML = "";
  const actions = view.scene.actions || [];

  if (!actions.length) {
    const p = document.createElement("p");
    p.textContent = view.game_over ? "本局已结束。" : "当前无可执行行动。";
    els.actions.appendChild(p);
    return;
  }

  actions.forEach((action) => {
    const button = document.createElement("button");
    button.className = "action-btn";
    const available = action.available !== false;
    button.disabled = view.game_over || !available;
    const hintParts = [];
    if (action.hint) {
      hintParts.push(action.hint);
    }
    if (action.cost && typeof action.cost === "object") {
      const parts = [];
      const main = Number(action.cost.main || 0);
      const bonus = Number(action.cost.bonus || 0);
      const move = Number(action.cost.move || 0);
      if (main > 0) {
        parts.push(`主${main}`);
      }
      if (bonus > 0) {
        parts.push(`副${bonus}`);
      }
      if (move > 0) {
        parts.push(`移${move}`);
      }
      if (parts.length) {
        hintParts.push(`消耗 ${parts.join("/")}`);
      }
    }
    if (action.turn_flow === "continue") {
      hintParts.push("可继续行动");
    } else if (action.turn_flow === "end") {
      hintParts.push("将结束回合");
    }
    if (!available) {
      hintParts.push(action.unavailable_detail || "当前不可执行");
      button.classList.add("is-unavailable");
    }
    const mergedHint = hintParts.join(" · ");
    button.innerHTML = `
      <div class="action-label">${escapeHtml(action.label)}</div>
      <div class="action-hint">${escapeHtml(mergedHint)}</div>
    `;
    button.addEventListener("click", async () => {
      try {
        const next = await api(`/api/game/${currentView.session_id}/action`, {
          method: "POST",
          body: JSON.stringify({ action_id: action.id }),
        });
        currentView = next;
        setRuntimeStatusMessage("", "neutral");
        render();
        await autoSave();
      } catch (error) {
        setRuntimeStatusMessage(`行动失败：${error.message}`, "error");
      }
    });
    els.actions.appendChild(button);
  });
}

/** Render the active encounter summary panel when an encounter is running. */
function renderEncounter(view) {
  const encounter = view.encounter;
  if (!encounter || !encounter.id) {
    els.encounterBox.hidden = true;
    els.encounterContent.innerHTML = "暂无遭遇。";
    return;
  }

  const blocks = [];
  const overviewRows = [`<div class="outcome-summary">${escapeHtml(encounter.title || "遭遇")}</div>`];

  const encounterMeta = [];
  encounterMeta.push(`第 ${Number(encounter.round || 1)} 轮`);
  if (encounter.phase_label || encounter.phase) {
    encounterMeta.push(`阶段：${escapeHtml(encounter.phase_label || encounter.phase)}`);
  }
  if (encounter.goal) {
    encounterMeta.push(`目标：${escapeHtml(encounter.goal)}`);
  }
  overviewRows.push(`<div class="outcome-detail">${encounterMeta.join(" · ")}</div>`);

  if (encounter.summary) {
    overviewRows.push(`<div>${escapeHtml(encounter.summary)}</div>`);
  }
  blocks.push(renderInfoSection("战况", overviewRows));

  if (typeof encounter.pressure === "number") {
    const pressureLabel = encounter.pressure_label || "压力";
    const pressureValue =
      Number(encounter.pressure_max || 0) > 0
        ? `${encounter.pressure}/${encounter.pressure_max}`
        : String(encounter.pressure);
    blocks.push(renderInfoSection("压力", [renderInfoLine(pressureLabel, escapeHtml(pressureValue))]));
  }

  if (encounter.economy && typeof encounter.economy === "object") {
    const budget = encounter.economy.budget || {};
    const spent = encounter.economy.spent || {};
    const remMain = Math.max(0, Number(budget.main || 0) - Number(spent.main || 0));
    const remBonus = Math.max(0, Number(budget.bonus || 0) - Number(spent.bonus || 0));
    const remMove = Math.max(0, Number(budget.move || 0) - Number(spent.move || 0));
    blocks.push(
      renderInfoSection("行动预算", [
        renderInfoLine(
          "预算",
          `主 ${remMain}/${Number(budget.main || 0)} · 副 ${remBonus}/${Number(budget.bonus || 0)} · 位移 ${remMove}/${Number(budget.move || 0)}`
        ),
      ])
    );
  }

  if (encounter.enemy && typeof encounter.enemy === "object") {
    const enemyParts = [];
    const hpLabel = resourceLabel("hp", "生命");
    const shieldLabel = resourceLabel("shield", "护盾");
    if (encounter.enemy.name) {
      enemyParts.push(`目标：${escapeHtml(encounter.enemy.name)}`);
    }
    if (encounter.enemy.intent) {
      enemyParts.push(`意图：${escapeHtml(encounter.enemy.intent)}`);
    }
    if (Number.isFinite(encounter.enemy.hp)) {
      const hpText =
        Number.isFinite(encounter.enemy.max_hp) && encounter.enemy.max_hp > 0
          ? `${encounter.enemy.hp}/${encounter.enemy.max_hp}`
          : `${encounter.enemy.hp}`;
      enemyParts.push(`敌方${escapeHtml(hpLabel)}：${escapeHtml(hpText)}`);
    }
    if (Number.isFinite(encounter.enemy.shield) && Number(encounter.enemy.shield) > 0) {
      enemyParts.push(`敌方${escapeHtml(shieldLabel)}：${escapeHtml(String(encounter.enemy.shield))}`);
    }
    if (enemyParts.length) {
      blocks.push(renderInfoSection("敌方", [renderInfoLine("状态", enemyParts.join(" · "))]));
    }
  }

  if (encounter.objective && typeof encounter.objective === "object") {
    const objectiveLabel = encounter.objective.label || "进度";
    const objectiveValue =
      Number.isFinite(encounter.objective.target) && encounter.objective.target > 0
        ? `${Number(encounter.objective.progress || 0)}/${Number(encounter.objective.target)}`
        : `${Number(encounter.objective.progress || 0)}`;
    blocks.push(renderInfoSection("目标进度", [renderInfoLine(objectiveLabel, escapeHtml(objectiveValue))]));
  }

  if (encounter.intent) {
    blocks.push(renderInfoSection("遭遇意图", [renderInfoLine("当前意图", escapeHtml(encounter.intent))]));
  }

  if (encounter.environment && typeof encounter.environment === "object") {
    const envMeta = encounter.environment_meta && typeof encounter.environment_meta === "object" ? encounter.environment_meta : {};
    const envParts = Object.entries(encounter.environment)
      .map(([field, value]) => {
        const metaEntry = envMeta[field] && typeof envMeta[field] === "object" ? envMeta[field] : {};
        const label = metaEntry.label || field;
        return `${escapeHtml(label)}：${escapeHtml(String(value))}`;
      })
      .filter(Boolean);
    if (envParts.length) {
      blocks.push(renderInfoSection("环境", [renderInfoLine("环境值", envParts.join(" · "))]));
    }
  }

  if (encounter.last_enemy_behavior && typeof encounter.last_enemy_behavior === "object") {
    blocks.push(renderInfoSection("敌方最近行动", [renderInfoLine("最近动作", escapeHtml(encounter.last_enemy_behavior.label || "未知"))]));
  }

  els.encounterBox.hidden = false;
  els.encounterContent.innerHTML = blocks.join("");
}

/** Render the player panel, resources, statuses, inventory, and recent log. */
function renderPlayer(view) {
  const player = view.player;
  els.playerSummary.textContent = `${player.name} · ${player.profession_name}`;

  const statEntries = Object.entries(player.stats)
    .map(([id, value]) => {
      const label = meta.stats[id]?.label || id;
      return `
        <div class="stat-item">
          <div class="stat-name">${escapeHtml(label)}</div>
          <div class="stat-value">${value}</div>
        </div>
      `;
    })
    .join("");
  els.statsGrid.innerHTML = statEntries;

  const skillEntries = Object.entries(player.skills || {})
    .filter(([, value]) => Number(value) > 0)
    .map(
      ([id, value]) => `
        <div class="stat-item">
          <div class="stat-name">${escapeHtml(skillLabel(id))}</div>
          <div class="stat-value">${value}</div>
        </div>
      `
    )
    .join("");
  els.skillGrid.innerHTML =
    skillEntries ||
    `
      <div class="stat-item">
        <div class="stat-name">技能</div>
        <div class="stat-value">无</div>
      </div>
    `;

  const corruptionLimit = Number.isFinite(player.corruption_limit) ? player.corruption_limit : 10;
  const hpLabel = resourceLabel("hp", "生命");
  const shieldLabel = resourceLabel("shield", "护盾");
  const corruptionLabel = resourceLabel("corruption", "腐化");
  const shillingsLabel = resourceLabel("shillings", "先令");
  const doomLabel = resourceLabel("doom", "末日进度");

  els.resourceGrid.innerHTML = `
    <div class="resource-item">
      <div class="resource-name">${escapeHtml(hpLabel)}</div>
      <div class="resource-value">${player.hp}/${player.max_hp}</div>
    </div>
    <div class="resource-item">
      <div class="resource-name">${escapeHtml(shieldLabel)}</div>
      <div class="resource-value">${Number(player.shield || 0)}</div>
    </div>
    <div class="resource-item">
      <div class="resource-name">${escapeHtml(corruptionLabel)}</div>
      <div class="resource-value">${player.corruption}/${corruptionLimit}</div>
    </div>
    <div class="resource-item">
      <div class="resource-name">${escapeHtml(shillingsLabel)}</div>
      <div class="resource-value">${player.shillings}</div>
    </div>
    <div class="resource-item">
      <div class="resource-name">${escapeHtml(doomLabel)}</div>
      <div class="resource-value">${view.progress.doom}</div>
    </div>
  `;

  if (view.statuses.length === 0) {
    els.statusList.innerHTML = `<span class="chip empty">暂无状态</span>`;
  } else {
    els.statusList.innerHTML = view.statuses
      .map((status) => {
        const duration =
          Number.isInteger(status.duration_turns) && Number(status.duration_turns) > 0
            ? ` · 剩余 ${status.duration_turns} 回合`
            : "";
        return `<span class="chip" title="${escapeHtml(`${status.description || ""}${duration}`)}">${escapeHtml(
          `${status.name}${duration}`
        )}</span>`;
      })
      .join("");
  }

  if (view.inventory.length === 0) {
    els.inventoryList.innerHTML = "<li>空</li>";
  } else {
    els.inventoryList.innerHTML = view.inventory
      .map(
        (item) =>
          `<li><strong>${escapeHtml(item.name)}</strong> ×${item.qty}<br /><small>${escapeHtml(item.description)}</small></li>`
      )
      .join("");
  }

  if (view.recent_log.length === 0) {
    els.logList.innerHTML = "<li>暂无记录</li>";
  } else {
    els.logList.innerHTML = view.recent_log.map((entry) => `<li>${escapeHtml(entry)}</li>`).join("");
  }
}

/** Render the main scene header and narrative text. */
function renderScene(view) {
  els.title.textContent = view.world.title;
  els.chapter.textContent = view.world.chapter_title;
  els.sceneTitle.textContent = view.scene.title;
  els.sceneMeta.textContent = `回合 ${view.progress.turns} · 末日 ${view.progress.doom}`;
  els.sceneText.textContent = view.scene.text;
}

/** Render the full active game view. */
function render() {
  if (!currentView) {
    return;
  }

  setToolbarEnabled(true);
  els.overlay.classList.remove("show");
  renderScene(currentView);
  renderOutcome(currentView.last_outcome);
  renderEncounter(currentView);
  renderActions(currentView);
  renderPlayer(currentView);
}

/** Ask the backend for the current session's canonical save payload. */
async function fetchCurrentSaveData() {
  if (!currentView) {
    return null;
  }
  return api(`/api/game/${currentView.session_id}/save`, { method: "POST" });
}

/** Write an autosave after successful state changes without blocking play. */
async function autoSave() {
  if (!currentView) {
    return;
  }
  try {
    const saveData = await fetchCurrentSaveData();
    writeAutosave(saveData, currentView);
  } catch {
    // Auto-save is best-effort and should never interrupt a successful action.
  }
}

/** Start a brand-new run using the setup form inputs. */
async function startNewGame() {
  const playerName = els.nameInput.value.trim();
  const professionId = els.professionSelect.value;
  pushFrontendDebug("start-new-game-clicked", {
    href: window.location.href,
    protocol: window.location.protocol,
    storyId: currentStoryId,
    professionId,
    playerNameLength: playerName.length,
  });

  try {
    const view = await api("/api/game/new", {
      method: "POST",
      body: JSON.stringify({ player_name: playerName, profession_id: professionId, story_id: currentStoryId }),
    });
    pushFrontendDebug("start-new-game-success", {
      sessionId: view.session_id,
      sceneId: view.scene?.id || null,
      storyId: view.world?.story_id || currentStoryId,
    });
    currentView = view;
    await syncMetaForView(view);
    setSetupStatus("");
    render();
    await autoSave();
  } catch (error) {
    pushFrontendDebug("start-new-game-failed", {
      message: error.message,
      href: window.location.href,
      protocol: window.location.protocol,
    });
    setSetupStatus(`创建失败：${error.message}`, true);
  }
}

/** Continue from the most recent autosave/manual save snapshot. */
async function continueFromSave() {
  const latest = latestSaveEntry();
  if (!latest?.save_data) {
    setSetupStatus("没有找到可继续的本地进度。", true);
    return;
  }

  try {
    const view = await api("/api/game/load", {
      method: "POST",
      body: JSON.stringify({ save_data: latest.save_data }),
    });
    currentView = view;
    await syncMetaForView(view);
    setSetupStatus("");
    render();
    await autoSave();
  } catch (error) {
    setSetupStatus(`继续失败：${error.message}`, true);
  }
}

/** Save the current run into the selected manual slot. */
async function handleManualSave() {
  if (!currentView) {
    return;
  }
  const slotId = els.slotSelect.value;
  try {
    const saveData = await fetchCurrentSaveData();
    upsertSlot(slotId, saveData, currentView, "manual");
    setSlotStatusMessage(`槽位 ${slotId} 已保存 · ${formatTime(saveData.saved_at)}`, "success");
  } catch (error) {
    setSlotStatusMessage(`槽位 ${slotId} 存档失败：${error.message}`, "error");
  }
}

/** Load the selected manual slot through the backend. */
async function handleManualLoad() {
  const slotId = els.slotSelect.value;
  const entry = slotEntry(slotId);
  if (!entry?.save_data) {
    setSlotStatusMessage(`槽位 ${slotId} 为空，无法读取。`, "error");
    return;
  }

  try {
    const view = await api("/api/game/load", {
      method: "POST",
      body: JSON.stringify({ save_data: entry.save_data }),
    });
    currentView = view;
    await syncMetaForView(view);
    render();
    await autoSave();
    setSlotStatusMessage(`已读取槽位 ${slotId} · ${entry.player_name || "未知角色"} · 回合 ${entry.turns ?? 0}`, "success");
  } catch (error) {
    setSlotStatusMessage(`槽位 ${slotId} 读档失败：${error.message}`, "error");
  }
}

/** Open the hidden file input used for importing saves. */
function triggerImport() {
  els.importInput.value = "";
  els.importInput.click();
}

/** Accept either a full export wrapper or a raw backend save payload. */
function extractImportedSaveData(parsed) {
  if (parsed && typeof parsed === "object") {
    if (parsed.save_data && typeof parsed.save_data === "object") {
      return parsed.save_data;
    }
    if (parsed.state && typeof parsed.state === "object") {
      return parsed;
    }
  }
  return null;
}

/** Import a save file, load it, then write it into the selected slot. */
async function handleImportFile(event) {
  const file = event.target.files?.[0];
  if (!file) {
    return;
  }
  const fileName = file.name || "未知文件";

  let parsed = null;
  try {
    const text = await file.text();
    parsed = JSON.parse(text);
  } catch {
    setSlotStatusMessage(`导入失败：${fileName} 不是有效 JSON。`, "error");
    return;
  }

  const saveData = extractImportedSaveData(parsed);
  if (!saveData) {
    setSlotStatusMessage(`导入失败：${fileName} 中未识别到有效存档结构。`, "error");
    return;
  }

  try {
    const view = await api("/api/game/load", {
      method: "POST",
      body: JSON.stringify({ save_data: saveData }),
    });
    currentView = view;
    await syncMetaForView(view);
    render();

    const refreshed = await fetchCurrentSaveData();
    const slotId = els.slotSelect.value;
    upsertSlot(slotId, refreshed, currentView, "import");
    writeAutosave(refreshed, currentView);
    setSlotStatusMessage(`导入成功：${fileName} -> 槽位 ${slotId}。`, "success");
  } catch (error) {
    setSlotStatusMessage(`导入失败：${fileName} · ${error.message}`, "error");
  }
}

/** Export the selected slot as a JSON file. */
function handleExport() {
  const slotId = els.slotSelect.value;
  const entry = slotEntry(slotId);
  if (!entry?.save_data) {
    setSlotStatusMessage(`槽位 ${slotId} 为空，无法导出。`, "error");
    return;
  }

  const exportPayload = {
    app: "lite-trpg-sim",
    export_type: "save_slot",
    exported_at: new Date().toISOString(),
    slot_id: slotId,
    save_data: entry.save_data,
  };

  const blob = new Blob([JSON.stringify(exportPayload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const stamp = new Date().toISOString().replaceAll(":", "-");
  const a = document.createElement("a");
  a.href = url;
  a.download = `lite-trpg-sim-slot-${slotId}-${stamp}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  setSlotStatusMessage(`已导出槽位 ${slotId} -> ${a.download}`, "success");
}

/** Reset the active run and reopen the setup overlay. */
function handleRestart() {
  if (!currentView) {
    return;
  }
  if (!window.confirm("确认重新开始？当前进行中的会话会被清空。")) {
    return;
  }
  currentView = null;
  setToolbarEnabled(false);
  els.overlay.classList.add("show");
  els.sceneTitle.textContent = "等待开始";
  els.sceneText.textContent = "";
  els.actions.innerHTML = "";
  els.outcomeContent.textContent = "尚无事件。";
  els.encounterBox.hidden = true;
  els.encounterContent.textContent = "暂无遭遇。";
}

/** Escape unsafe text before inserting it into HTML strings. */
function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

/** Boot the frontend, fetch initial metadata, and bind UI events. */
async function init() {
  pushFrontendDebug("frontend-init", {
    href: window.location.href,
    protocol: window.location.protocol,
  });
  setToolbarEnabled(false);
  els.actions.innerHTML = "";

  refreshSlotOptions();
  refreshSlotStatus();

  try {
    await loadMetaForStory(null);
  } catch (error) {
    setSetupStatus(`无法连接后端：${error.message}`, true);
    return;
  }

  els.slotSelect.addEventListener("change", () => {
    setActiveSlotId(els.slotSelect.value);
    refreshSlotStatus();
  });

  const activeSlot = getActiveSlotId();
  els.slotSelect.value = activeSlot;

  els.professionSelect.addEventListener("change", renderProfessionPreview);
  els.storySelect.addEventListener("change", async () => {
    const storyId = els.storySelect.value;
    try {
      await loadMetaForStory(storyId);
      setSetupStatus("");
    } catch (error) {
      setSetupStatus(`切换故事失败：${error.message}`, true);
    }
  });
  els.newGameBtn.addEventListener("click", startNewGame);
  els.continueBtn.addEventListener("click", continueFromSave);
  els.saveBtn.addEventListener("click", handleManualSave);
  els.loadBtn.addEventListener("click", handleManualLoad);
  els.exportBtn.addEventListener("click", handleExport);
  els.importBtn.addEventListener("click", triggerImport);
  els.importInput.addEventListener("change", handleImportFile);
  els.restartBtn.addEventListener("click", handleRestart);

  if (hasAnySaveEntry()) {
    setSetupStatus("检测到本地存档，可继续最近进度或从槽位读取。", false);
  }
}

init();
