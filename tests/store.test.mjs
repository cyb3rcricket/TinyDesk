import assert from "node:assert/strict";
import { test } from "node:test";
const storeHref = new URL("../js/store.js", import.meta.url).href;
const analysisHref = new URL("../js/analysis.js", import.meta.url).href;
const STORAGE_KEY = "tinydesk.tickets.v1";

let instance = 0;

function installStorage() {
  const data = new Map();
  const storage = {
    getItem(key) {
      return data.has(key) ? data.get(key) : null;
    },
    setItem(key, value) {
      data.set(String(key), String(value));
    },
    removeItem(key) {
      data.delete(key);
    },
    clear() {
      data.clear();
    }
  };
  globalThis.localStorage = storage;
  return { data, storage };
}

async function loadStore() {
  instance += 1;
  return import(`${storeHref}?instance=${instance}`);
}

test("reopening a resolved ticket clears the note and the analyze payload", async () => {
  installStorage();
  const store = await loadStore();
  const before = store.getTicket("TD-2408");
  assert.equal(before.status, "Resolved");
  assert.equal(
    before.resolutionNote,
    "Replaced the keyboard on loaner LP-14 and confirmed typing in the facilities log."
  );

  const resolved = store.saveTicketFields("TD-2408", {
    category: "Hardware",
    priority: "Low",
    status: "Resolved",
    resolutionNote: before.resolutionNote
  });
  assert.equal(resolved.ok, true);
  assert.equal(resolved.unchanged, true);

  const reopened = store.saveTicketFields("TD-2408", {
    category: "Hardware",
    priority: "Low",
    status: "In Progress",
    resolutionNote: before.resolutionNote
  });
  assert.equal(reopened.ok, true);
  assert.equal(reopened.ticket.status, "In Progress");
  assert.equal(reopened.ticket.resolutionNote, "");
  const statusLine = reopened.ticket.activity.at(-1);
  assert.equal(statusLine.kind, "status");
  assert.equal(
    statusLine.body,
    "Status changed from Resolved to In Progress. Resolution note cleared."
  );

  const stored = store.getTicket("TD-2408");
  assert.equal(stored.resolutionNote, "");
  assert.equal(stored.status, "In Progress");

  let captured = null;
  globalThis.fetch = async (_url, options) => {
    captured = JSON.parse(options.body);
    return {
      ok: true,
      json: async () => ({
        available: true,
        summary: "The loaner keyboard was replaced, then the ticket was reopened.",
        suggestedCategory: "Hardware",
        followUps: [],
        draft: "Hello Theo,\n\nAshmere Press IT"
      })
    };
  };
  const { analyzeTicket } = await import(`${analysisHref}?instance=${instance}`);
  const analysis = await analyzeTicket(stored);
  assert.equal(analysis.available, true);
  assert.equal(captured.resolutionNote, "");
  assert.equal(captured.status, "In Progress");
  assert.equal(captured.id, "TD-2408");
});

test("resolving still stores the resolution note", async () => {
  installStorage();
  const store = await loadStore();
  const saved = store.saveTicketFields("TD-2402", {
    category: "Other",
    priority: "Medium",
    status: "Resolved",
    resolutionNote: "Reset the password."
  });
  assert.equal(saved.ok, true);
  assert.equal(saved.ticket.resolutionNote, "Reset the password.");
  assert.match(saved.ticket.activity.at(-1).body, /Resolution: Reset the password\./);
  assert.equal(store.getTicket("TD-2402").resolutionNote, "Reset the password.");
});

test("an earlier tab keeps a ticket created in another tab", async () => {
  installStorage();
  const tabA = await loadStore();
  assert.equal(tabA.getTickets().some((ticket) => ticket.subject === "Tab B ticket"), false);

  const tabB = await loadStore();
  const created = tabB.createTicket({
    requester: "Ada Lovelace",
    subject: "Tab B ticket",
    description: "Created in the other tab.",
    category: "Software"
  });
  assert.equal(created.ok, true);

  const saved = tabA.saveTicketFields("TD-2404", {
    category: "Software",
    priority: "High",
    status: "New",
    resolutionNote: ""
  });
  assert.equal(saved.ok, true);
  assert.equal(saved.ticket.priority, "High");

  const fromA = tabA.getTicket(created.ticket.id);
  const fromB = tabB.getTicket(created.ticket.id);
  assert.ok(fromA);
  assert.equal(fromA.subject, "Tab B ticket");
  assert.equal(fromB.subject, "Tab B ticket");
  assert.equal(tabA.getTicket("TD-2404").priority, "High");
  assert.equal(tabB.getTickets().length, tabA.getTickets().length);
});

test("a failed localStorage write is returned as an error", async () => {
  const { data } = installStorage();
  const store = await loadStore();
  store.getTickets();
  const before = data.get(STORAGE_KEY);
  globalThis.localStorage.setItem = () => {
    throw new Error("quota");
  };

  const result = store.saveTicketFields("TD-2401", {
    category: "Network",
    priority: "Low",
    status: "In Progress",
    resolutionNote: ""
  });

  assert.equal(result.ok, false);
  assert.equal(
    result.error,
    "The latest change could not be saved in this browser. It will disappear when you close the tab."
  );
  assert.equal(store.getStorageWarning(), result.error);
  assert.equal(data.get(STORAGE_KEY), before);
  assert.equal(store.getTicket("TD-2401").priority, "High");
});
