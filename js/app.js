import { analyzeTicket } from "./analysis.js";
import {
  CATEGORIES,
  PRIORITIES,
  STATUSES,
  addUpdate,
  createTicket,
  formatTimestamp,
  getStorageWarning,
  getTicket,
  getTickets,
  resetDemoData,
  saveTicketFields
} from "./store.js";

const KIND_LABEL = {
  opened: "Opened",
  field: "Details",
  status: "Status change",
  internal: "Internal note",
  reply: "Reply to requester"
};

const STATUS_CLASS = {
  New: "status-new",
  "In Progress": "status-progress",
  "Waiting on User": "status-waiting",
  Resolved: "status-resolved"
};

const PRIORITY_CLASS = {
  Low: "priority-low",
  Medium: "priority-medium",
  High: "priority-high"
};

const els = {};
let selectedId = "";
let currentTicketId = "";
let booted = false;
let keepBanner = false;

function must(id) {
  const node = document.getElementById(id);
  if (!node) throw new Error(`Missing #${id}`);
  return node;
}

function cacheElements() {
  [
    "reset-demo",
    "app-banner",
    "view-queue",
    "queue-heading",
    "filter-form",
    "search",
    "filter-status",
    "filter-category",
    "clear-filters",
    "queue-count",
    "ticket-table",
    "ticket-rows",
    "ticket-cards",
    "empty-state",
    "empty-message",
    "empty-clear",
    "empty-new",
    "view-new",
    "new-heading",
    "new-form",
    "new-requester",
    "new-department",
    "new-subject",
    "new-description",
    "new-category",
    "new-form-status",
    "view-ticket",
    "ticket-missing",
    "missing-heading",
    "ticket-workspace",
    "ws-id",
    "ws-subject",
    "ws-requester",
    "ws-department",
    "ws-created",
    "ws-updated",
    "ws-description",
    "fields-form",
    "field-category",
    "field-priority",
    "field-status",
    "resolution-wrap",
    "field-resolution",
    "save-status",
    "activity-list",
    "update-form",
    "update-body",
    "composer-hint",
    "update-submit",
    "update-status",
    "analyze-btn",
    "analysis-output",
    "confirm-dialog",
    "confirm-title",
    "confirm-message",
    "confirm-cancel",
    "confirm-ok"
  ].forEach((id) => {
    els[id] = must(id);
  });
}

function fillSelect(select, values, placeholder) {
  select.replaceChildren();
  if (placeholder) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = placeholder;
    select.append(option);
  }
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.append(option);
  });
}

function badge(text, className) {
  const node = document.createElement("span");
  node.className = `badge ${className}`;
  node.textContent = text;
  return node;
}

function showBanner(message, tone) {
  keepBanner = Boolean(message);
  els["app-banner"].hidden = !message;
  els["app-banner"].textContent = message || "";
  els["app-banner"].className = tone === "error" ? "banner is-error" : "banner";
}

function noteStorage() {
  const warning = getStorageWarning();
  if (warning) showBanner(warning, "error");
}

function setStatus(node, message, tone) {
  node.textContent = message || "";
  node.className = tone ? `form-status is-${tone}` : "form-status";
}

function parseRoute() {
  const hash = location.hash || "#/";
  if (hash === "#/" || hash === "#" || hash === "") return { name: "queue" };
  if (hash === "#/new") return { name: "new" };
  const prefix = "#/ticket/";
  if (hash.startsWith(prefix)) {
    return { name: "ticket", id: decodeURIComponent(hash.slice(prefix.length)) };
  }
  return { name: "queue" };
}

function filtersActive() {
  return Boolean(
    els.search.value.trim() || els["filter-status"].value || els["filter-category"].value
  );
}

function visibleTickets() {
  const query = els.search.value.trim().toLowerCase();
  const status = els["filter-status"].value;
  const category = els["filter-category"].value;
  return getTickets().filter((ticket) => {
    if (status && ticket.status !== status) return false;
    if (category && ticket.category !== category) return false;
    if (!query) return true;
    return `${ticket.id} ${ticket.subject}`.toLowerCase().includes(query);
  });
}

function ticketHref(id) {
  return `#/ticket/${encodeURIComponent(id)}`;
}

function appendPair(list, label, valueNode) {
  const wrap = document.createElement("div");
  const term = document.createElement("dt");
  term.textContent = label;
  const detail = document.createElement("dd");
  if (typeof valueNode === "string") detail.textContent = valueNode;
  else detail.append(valueNode);
  wrap.append(term, detail);
  list.append(wrap);
}

function renderQueue() {
  const all = getTickets();
  const tickets = visibleTickets();
  const active = filtersActive();
  els["clear-filters"].hidden = !active;
  els["queue-count"].textContent = active
    ? `Showing ${tickets.length} of ${all.length} tickets`
    : `${all.length} ticket${all.length === 1 ? "" : "s"}`;

  els["ticket-rows"].replaceChildren();
  els["ticket-cards"].replaceChildren();

  tickets.forEach((ticket) => {
    els["ticket-rows"].append(renderRow(ticket));
    els["ticket-cards"].append(renderCard(ticket));
  });

  const empty = tickets.length === 0;
  els["ticket-table"].hidden = empty;
  els["ticket-cards"].hidden = empty;
  els["empty-state"].hidden = !empty;
  if (empty) {
    const noTickets = all.length === 0;
    els["empty-message"].textContent = noTickets
      ? "No tickets yet. Create one to start the queue."
      : "No tickets match this search or filter.";
    els["empty-clear"].hidden = noTickets || !active;
    els["empty-new"].hidden = !noTickets;
  }

  document.title = "Ticket queue · TinyDesk";
  return els["queue-heading"];
}

function renderRow(ticket) {
  const row = document.createElement("tr");
  if (ticket.id === selectedId) row.className = "is-selected";
  row.append(
    cellLink(ticket),
    textCell(ticket.subject, "subject-cell"),
    textCell(ticket.requester),
    textCell(ticket.category),
    badgeCell(ticket.priority, PRIORITY_CLASS[ticket.priority]),
    badgeCell(ticket.status, STATUS_CLASS[ticket.status]),
    timeCell(ticket.updatedAt)
  );
  row.addEventListener("click", (event) => {
    if (event.target.closest("a")) return;
    location.hash = ticketHref(ticket.id);
  });
  return row;
}

function cellLink(ticket) {
  const cell = document.createElement("td");
  const link = document.createElement("a");
  link.href = ticketHref(ticket.id);
  link.className = "mono";
  link.textContent = ticket.id;
  const extra = document.createElement("span");
  extra.className = "sr-only";
  extra.textContent = `: ${ticket.subject}`;
  link.append(extra);
  cell.append(link);
  return cell;
}

function textCell(value, className) {
  const cell = document.createElement("td");
  if (className) cell.className = className;
  cell.textContent = value;
  return cell;
}

function badgeCell(value, className) {
  const cell = document.createElement("td");
  cell.append(badge(value, className || ""));
  return cell;
}

function timeCell(iso) {
  const cell = document.createElement("td");
  const time = document.createElement("time");
  time.className = "mono";
  time.dateTime = iso;
  time.textContent = formatTimestamp(iso);
  cell.append(time);
  return cell;
}

function renderCard(ticket) {
  const link = document.createElement("a");
  link.className = ticket.id === selectedId ? "ticket-card is-selected" : "ticket-card";
  link.href = ticketHref(ticket.id);
  const id = document.createElement("span");
  id.className = "card-id";
  id.textContent = ticket.id;
  const subject = document.createElement("span");
  subject.className = "card-subject";
  subject.textContent = ticket.subject;
  const list = document.createElement("dl");
  appendPair(list, "Requester", ticket.requester);
  appendPair(list, "Category", ticket.category);
  appendPair(list, "Priority", badge(ticket.priority, PRIORITY_CLASS[ticket.priority] || ""));
  appendPair(list, "Status", badge(ticket.status, STATUS_CLASS[ticket.status] || ""));
  appendPair(list, "Updated", formatTimestamp(ticket.updatedAt));
  link.append(id, subject, list);
  return link;
}

function renderNew() {
  els["new-form"].reset();
  els["new-requester"].removeAttribute("aria-invalid");
  els["new-subject"].removeAttribute("aria-invalid");
  els["new-description"].removeAttribute("aria-invalid");
  els["new-category"].removeAttribute("aria-invalid");
  setStatus(els["new-form-status"], "");
  document.title = "New ticket · TinyDesk";
  return els["new-heading"];
}

function paintTicket(ticket) {
  els["ws-id"].textContent = ticket.id;
  els["ws-subject"].textContent = ticket.subject;
  els["ws-requester"].textContent = ticket.requester;
  els["ws-department"].textContent = ticket.department || "Not specified";
  els["ws-created"].dateTime = ticket.createdAt;
  els["ws-created"].textContent = formatTimestamp(ticket.createdAt);
  els["ws-updated"].dateTime = ticket.updatedAt;
  els["ws-updated"].textContent = formatTimestamp(ticket.updatedAt);
  els["ws-description"].textContent = ticket.description;
  renderActivity(ticket.activity);
  document.title = `${ticket.id} · TinyDesk`;
}

function renderTicket(id) {
  currentTicketId = id;
  selectedId = id;
  const ticket = getTicket(id);
  const found = Boolean(ticket);
  els["ticket-missing"].hidden = found;
  els["ticket-workspace"].hidden = !found;
  els["analysis-output"].replaceChildren();
  if (!found) {
    document.title = "Ticket not found · TinyDesk";
    return els["missing-heading"];
  }

  paintTicket(ticket);
  els["field-category"].value = ticket.category;
  els["field-priority"].value = ticket.priority;
  els["field-status"].value = ticket.status;
  els["field-resolution"].value = ticket.resolutionNote || "";
  syncResolutionField();
  setStatus(els["save-status"], "");
  els["update-body"].value = "";
  els["update-form"].elements["update-kind"].value = "internal";
  syncComposerMode();
  setStatus(els["update-status"], "");
  return els["ws-subject"];
}

function renderActivity(activity) {
  const items = activity
    .map((item, index) => ({ item, index }))
    .sort((a, b) => a.item.at.localeCompare(b.item.at) || a.index - b.index)
    .map((entry) => entry.item);

  els["activity-list"].replaceChildren();
  items.forEach((item) => {
    const li = document.createElement("li");
    li.className = `activity-item activity-${item.kind || "opened"}`;
    const meta = document.createElement("div");
    meta.className = "activity-meta";
    const label = document.createElement("span");
    label.className = "activity-label";
    label.textContent = KIND_LABEL[item.kind] || "Update";
    const time = document.createElement("time");
    time.className = "mono activity-time";
    time.dateTime = item.at || "";
    time.textContent = formatTimestamp(item.at);
    meta.append(label, time);
    const body = document.createElement("p");
    body.className = "activity-body";
    body.textContent = item.body || "";
    li.append(meta, body);
    if (item.kind === "internal") {
      const caption = document.createElement("p");
      caption.className = "activity-caption";
      caption.textContent = "Internal note. Not sent to the requester.";
      li.append(caption);
    }
    if (item.kind === "reply") {
      const caption = document.createElement("p");
      caption.className = "activity-caption";
      caption.textContent = "Simulated reply. Saved in this demo only. No email was sent.";
      li.append(caption);
    }
    els["activity-list"].append(li);
  });
}

function syncResolutionField() {
  const resolved = els["field-status"].value === "Resolved";
  els["resolution-wrap"].hidden = !resolved;
  els["field-resolution"].disabled = !resolved;
  if (resolved) els["field-resolution"].setAttribute("aria-required", "true");
  else {
    els["field-resolution"].removeAttribute("aria-required");
    els["field-resolution"].removeAttribute("aria-invalid");
  }
}

function syncComposerMode() {
  const reply = els["update-form"].elements["update-kind"].value === "reply";
  els["composer-hint"].textContent = reply
    ? "This reply is saved in the demo only. TinyDesk does not send email."
    : "Internal notes stay in the ticket history. They are not sent to the requester.";
  els["update-submit"].textContent = reply ? "Save reply" : "Save internal note";
}

function renderRoute() {
  if (keepBanner) keepBanner = false;
  else if (booted) showBanner("");

  const route = parseRoute();
  els["view-queue"].hidden = route.name !== "queue";
  els["view-new"].hidden = route.name !== "new";
  els["view-ticket"].hidden = route.name !== "ticket";

  let heading = els["queue-heading"];
  if (route.name === "queue") heading = renderQueue();
  if (route.name === "new") heading = renderNew();
  if (route.name === "ticket") heading = renderTicket(route.id);

  if (booted && heading) {
    heading.setAttribute("tabindex", "-1");
    heading.focus();
  }
  booted = true;
}

function askConfirm({ title, message, confirmLabel }) {
  els["confirm-title"].textContent = title;
  els["confirm-message"].textContent = message;
  els["confirm-ok"].textContent = confirmLabel || "Confirm";
  const dialog = els["confirm-dialog"];
  return new Promise((resolve) => {
    const onOk = () => dialog.close("confirm");
    const onCancel = () => dialog.close("cancel");
    const onClose = () => {
      els["confirm-ok"].removeEventListener("click", onOk);
      els["confirm-cancel"].removeEventListener("click", onCancel);
      dialog.removeEventListener("close", onClose);
      resolve(dialog.returnValue === "confirm");
    };
    els["confirm-ok"].addEventListener("click", onOk);
    els["confirm-cancel"].addEventListener("click", onCancel);
    dialog.addEventListener("close", onClose);
    dialog.showModal();
  });
}

function onCreateTicket(event) {
  event.preventDefault();
  const fields = [
    els["new-requester"],
    els["new-subject"],
    els["new-description"],
    els["new-category"]
  ];
  fields.forEach((field) => field.removeAttribute("aria-invalid"));
  const result = createTicket({
    requester: els["new-requester"].value,
    department: els["new-department"].value,
    subject: els["new-subject"].value,
    description: els["new-description"].value,
    category: els["new-category"].value
  });
  if (!result.ok) {
    if (!els["new-requester"].value.trim()) els["new-requester"].setAttribute("aria-invalid", "true");
    if (!els["new-subject"].value.trim()) els["new-subject"].setAttribute("aria-invalid", "true");
    if (!els["new-description"].value.trim()) els["new-description"].setAttribute("aria-invalid", "true");
    if (!els["new-category"].value) els["new-category"].setAttribute("aria-invalid", "true");
    setStatus(els["new-form-status"], result.error, "error");
    const firstInvalid = fields.find((field) => field.getAttribute("aria-invalid") === "true");
    if (firstInvalid) firstInvalid.focus();
    return;
  }
  if (getStorageWarning()) noteStorage();
  else showBanner(`Ticket ${result.ticket.id} created.`);
  location.hash = ticketHref(result.ticket.id);
}

function onSaveFields(event) {
  event.preventDefault();
  const result = saveTicketFields(currentTicketId, {
    category: els["field-category"].value,
    priority: els["field-priority"].value,
    status: els["field-status"].value,
    resolutionNote: els["field-resolution"].value
  });
  if (!result.ok) {
    setStatus(els["save-status"], result.error, "error");
    if (els["field-status"].value === "Resolved") {
      els["field-resolution"].setAttribute("aria-invalid", "true");
      els["field-resolution"].focus();
    }
    return;
  }
  els["field-resolution"].removeAttribute("aria-invalid");
  if (result.unchanged) {
    setStatus(els["save-status"], "No changes to save.");
    return;
  }
  paintTicket(result.ticket);
  els["field-resolution"].value = result.ticket.resolutionNote || "";
  setStatus(els["save-status"], "Changes saved.", "ok");
  noteStorage();
}

function onAddUpdate(event) {
  event.preventDefault();
  const kind = els["update-form"].elements["update-kind"].value;
  const result = addUpdate(currentTicketId, {
    kind,
    body: els["update-body"].value
  });
  if (!result.ok) {
    setStatus(els["update-status"], result.error, "error");
    els["update-body"].focus();
    return;
  }
  els["update-body"].value = "";
  paintTicket(result.ticket);
  const message = kind === "reply"
    ? "Reply saved in this demo. No email was sent."
    : "Internal note saved.";
  setStatus(els["update-status"], message, "ok");
  noteStorage();
}

function renderAnalysis(result) {
  const output = els["analysis-output"];
  output.replaceChildren();
  if (!result || result.available !== true) {
    const box = document.createElement("div");
    box.className = "placeholder-note";
    const paragraph = document.createElement("p");
    paragraph.textContent = result && result.message
      ? result.message
      : "Analysis did not return a suggestion.";
    box.append(paragraph);
    output.append(box);
    return;
  }

  const note = document.createElement("p");
  note.className = "sample-note";
  note.textContent = "Prepared sample for this demo ticket. Not a live model response.";
  output.append(note);
  addAnalysisBlock(output, "Issue summary", result.summary);
  addAnalysisBlock(output, "Suggested category", result.suggestedCategory);

  const questions = document.createElement("h3");
  questions.textContent = "Missing information";
  output.append(questions);
  const followUps = Array.isArray(result.followUps) ? result.followUps : [];
  if (!followUps.length) {
    const none = document.createElement("p");
    none.textContent = "No follow-up questions for this sample.";
    output.append(none);
  } else {
    const list = document.createElement("ul");
    followUps.forEach((question) => {
      const item = document.createElement("li");
      item.textContent = question;
      list.append(item);
    });
    output.append(list);
  }
  addAnalysisBlock(output, "Draft response", result.draft);

  const actions = document.createElement("div");
  actions.className = "assist-actions";
  const apply = document.createElement("button");
  apply.type = "button";
  apply.className = "btn";
  apply.textContent = "Apply category";
  apply.addEventListener("click", () => applyCategory(result.suggestedCategory));
  const useDraft = document.createElement("button");
  useDraft.type = "button";
  useDraft.className = "btn btn-primary";
  useDraft.textContent = "Use draft";
  useDraft.addEventListener("click", () => useDraftResponse(result.draft));
  actions.append(apply, useDraft);
  output.append(actions);
}

function addAnalysisBlock(parent, title, text) {
  const heading = document.createElement("h3");
  heading.textContent = title;
  const paragraph = document.createElement("p");
  paragraph.className = title === "Draft response" ? "draft-text" : "";
  paragraph.textContent = text || "";
  parent.append(heading, paragraph);
}

function applyCategory(category) {
  if (!CATEGORIES.includes(category)) {
    setStatus(
      els["save-status"],
      "That suggestion is not one of the TinyDesk categories, so it was not applied.",
      "error"
    );
    return;
  }
  els["field-category"].value = category;
  els["field-category"].focus();
  setStatus(els["save-status"], `Category set to ${category}. Save changes to keep it.`);
}

async function useDraftResponse(draft) {
  const existing = els["update-body"].value.trim();
  if (existing) {
    const ok = await askConfirm({
      title: "Replace composer text?",
      message: "The composer already has text. Replace it with the suggested draft? You can still edit the draft before saving.",
      confirmLabel: "Replace text"
    });
    if (!ok) return;
  }
  els["update-form"].elements["update-kind"].value = "reply";
  syncComposerMode();
  els["update-body"].value = draft;
  els["update-body"].focus();
  setStatus(els["update-status"], "Draft placed in the reply composer. Review it before saving. No email is sent.");
}

async function onAnalyze() {
  const ticket = getTicket(currentTicketId);
  if (!ticket) return;
  try {
    const result = await analyzeTicket(ticket);
    renderAnalysis(result);
  } catch {
    renderAnalysis({
      available: false,
      message: "Analysis could not be completed. Nothing here is model output."
    });
  }
}

async function onReset() {
  const ok = await askConfirm({
    title: "Reset demo data?",
    message: "This discards every saved ticket, edit, and activity note, and restores the original sample tickets.",
    confirmLabel: "Reset demo data"
  });
  if (!ok) return;
  resetDemoData();
  selectedId = "";
  currentTicketId = "";
  showBanner("Demo data restored.");
  noteStorage();
  if ((location.hash || "#/") !== "#/") location.hash = "#/";
  else renderRoute();
}

function onKeydown(event) {
  if (event.key !== "Escape") return;
  if (els["confirm-dialog"].open) return;
  if (parseRoute().name === "queue") return;
  const tag = document.activeElement && document.activeElement.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
  location.hash = "#/";
}

function bindEvents() {
  els["filter-form"].addEventListener("submit", (event) => event.preventDefault());
  els.search.addEventListener("input", renderQueue);
  els.search.addEventListener("search", renderQueue);
  els["filter-status"].addEventListener("change", renderQueue);
  els["filter-category"].addEventListener("change", renderQueue);
  els["clear-filters"].addEventListener("click", clearFilters);
  els["empty-clear"].addEventListener("click", clearFilters);
  els["reset-demo"].addEventListener("click", onReset);
  els["new-form"].addEventListener("submit", onCreateTicket);
  els["fields-form"].addEventListener("submit", onSaveFields);
  els["fields-form"].addEventListener("input", () => {
    if (els["save-status"].textContent) setStatus(els["save-status"], "");
  });
  els["field-status"].addEventListener("change", syncResolutionField);
  els["update-form"].addEventListener("submit", onAddUpdate);
  els["update-form"].addEventListener("change", syncComposerMode);
  els["update-form"].addEventListener("input", () => {
    if (els["update-status"].textContent) setStatus(els["update-status"], "");
  });
  els["analyze-btn"].addEventListener("click", onAnalyze);
  window.addEventListener("hashchange", renderRoute);
  document.addEventListener("keydown", onKeydown);
}

function clearFilters() {
  els.search.value = "";
  els["filter-status"].value = "";
  els["filter-category"].value = "";
  renderQueue();
  els.search.focus();
}

function init() {
  cacheElements();
  fillSelect(els["filter-status"], STATUSES, "All statuses");
  fillSelect(els["filter-category"], CATEGORIES, "All categories");
  fillSelect(els["field-category"], CATEGORIES);
  fillSelect(els["field-priority"], PRIORITIES);
  fillSelect(els["field-status"], STATUSES);
  fillSelect(els["new-category"], CATEGORIES, "Choose a category");
  bindEvents();
  syncComposerMode();
  renderRoute();
  noteStorage();
}

init();
