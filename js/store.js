/**
 * Ticket store for TinyDesk.
 * Seeds demo data once, then keeps tickets and activity in localStorage.
 */

const STORAGE_KEY = "tinydesk.tickets.v1";

export const STATUSES = ["New", "In Progress", "Waiting on User", "Resolved"];
export const PRIORITIES = ["Low", "Medium", "High"];
export const CATEGORIES = ["Access", "Network", "Hardware", "Software", "Email", "Other"];

let cache = null;
let storageWarning = "";

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function at(month, day, hour, minute) {
  return new Date(Date.UTC(2026, month - 1, day, hour, minute)).toISOString();
}

function act(kind, body, month, day, hour, minute) {
  const stamp = at(month, day, hour, minute);
  return { id: `seed-${kind}-${stamp}`, kind, body, at: stamp };
}

function buildTicket(fields) {
  const activity = fields.activity;
  return {
    seeded: true,
    resolutionNote: "",
    ...fields,
    updatedAt: activity[activity.length - 1].at
  };
}

function createSeed() {
  return [
    buildTicket({
      id: "TD-2401",
      subject: "Home VPN will not connect",
      requester: "Mara Ellison",
      department: "Editorial",
      category: "Network",
      priority: "High",
      status: "In Progress",
      description:
        "I am working from home today and the Ashmere VPN client stops at \"contacting gateway.\" It worked on Thursday from the office. I need the style guide share before the afternoon proof.",
      createdAt: at(9, 28, 14, 12),
      activity: [
        act("opened", "Ticket created.", 9, 28, 14, 12),
        act("status", "Status changed from New to In Progress.", 9, 28, 14, 40),
        act(
          "internal",
          "Checked the Ashmere VPN profile on Mara's laptop record. The client is installed. Still need the error text from the home connection.",
          9,
          28,
          15,
          5
        ),
        act(
          "internal",
          "Mara pinged again before the afternoon proof. Still blocked at contacting gateway.",
          10,
          1,
          9,
          20
        )
      ]
    }),
    buildTicket({
      id: "TD-2402",
      subject: "Password reset",
      requester: "Jonah Peck",
      department: "Finance",
      category: "Other",
      priority: "Medium",
      status: "New",
      description: "Can't get in. Please reset.",
      createdAt: at(10, 1, 8, 22),
      activity: [act("opened", "Ticket created.", 10, 1, 8, 22)]
    }),
    buildTicket({
      id: "TD-2403",
      subject: "Production printer is ignoring jobs",
      requester: "Priya Nand",
      department: "Production",
      category: "Hardware",
      priority: "Medium",
      status: "Waiting on User",
      description:
        "Jobs sent to the floor printer sit in the queue and never come out. We are trying to print the galley for the Vale anthology. Other people may be affected. I tried restarting my computer once.",
      createdAt: at(9, 29, 11, 4),
      activity: [
        act("opened", "Ticket created.", 9, 29, 11, 4),
        act(
          "internal",
          "Print server production-02 shows several jobs sitting in Printing for the floor queue.",
          9,
          29,
          11,
          20
        ),
        act(
          "reply",
          "Hello Priya,\n\nI can see jobs stuck in the production queue. Which printer name are you choosing, and does the printer panel show a code or a jam?\n\nAshmere Press IT",
          9,
          29,
          11,
          26
        ),
        act("status", "Status changed from New to Waiting on User.", 9, 29, 11, 27)
      ]
    }),
    buildTicket({
      id: "TD-2404",
      subject: "Install Larkspur for the cover layout",
      requester: "Cole Brennan",
      department: "Design",
      category: "Software",
      priority: "Low",
      status: "New",
      description:
        "Please install Larkspur Layout 4 on my design machine, DS-14. I have a cover due Friday and the trial copy expired. I am on the current Ashmere image.",
      createdAt: at(9, 30, 10, 15),
      activity: [act("opened", "Ticket created.", 9, 30, 10, 15)]
    }),
    buildTicket({
      id: "TD-2405",
      subject: "Mail from outside Ashmere is not arriving",
      requester: "Elise Voss",
      department: "Communications",
      category: "Email",
      priority: "High",
      status: "In Progress",
      description:
        "Since Monday I have not received messages from authors. Internal mail still works. I checked the junk folder. One author said their message did not bounce. It just never showed up.",
      createdAt: at(9, 27, 9, 12),
      activity: [
        act("opened", "Ticket created.", 9, 27, 9, 12),
        act("status", "Status changed from New to In Progress.", 9, 27, 9, 40),
        act(
          "internal",
          "Gateway log shows accepted connections from inside Ashmere and no recent mail from the outside domains on the communications list. No bounce is generated when a message is dropped at the spam threshold.",
          10,
          1,
          7,
          48
        )
      ]
    }),
    buildTicket({
      id: "TD-2406",
      subject: "Need access",
      requester: "Samir Adeyemi",
      department: "Archives",
      category: "Access",
      priority: "Medium",
      status: "New",
      description: "I need access to the thing from last week. It is urgent for the reading room.",
      createdAt: at(10, 1, 9, 41),
      activity: [act("opened", "Ticket created.", 10, 1, 9, 41)]
    }),
    buildTicket({
      id: "TD-2407",
      subject: "VPN drops every few minutes",
      requester: "Ruth Calder",
      department: "Field Desk",
      category: "Network",
      priority: "Medium",
      status: "New",
      description:
        "When I am on a site visit the VPN connects, then disconnects after about ten minutes. I was on a public library wifi today. Reconnecting works until it drops again. Chat stays open, but the archive share disappears.",
      createdAt: at(9, 30, 15, 8),
      activity: [act("opened", "Ticket created.", 9, 30, 15, 8)]
    }),
    buildTicket({
      id: "TD-2408",
      subject: "Sticky keys on loaner laptop LP-14",
      requester: "Theo Lang",
      department: "Facilities",
      category: "Hardware",
      priority: "Low",
      status: "Resolved",
      resolutionNote: "Replaced the keyboard on loaner LP-14 and confirmed typing in the facilities log.",
      description:
        "The loaner laptop for the loading dock repeats letters. I turned off the accessibility sticky keys setting and it still happens. Mostly the E and O keys.",
      createdAt: at(9, 24, 13, 22),
      activity: [
        act("opened", "Ticket created.", 9, 24, 13, 22),
        act("status", "Status changed from New to In Progress.", 9, 24, 13, 40),
        act(
          "internal",
          "Accessibility sticky keys was already off. The E and O keys repeat when the dock loaner is tilted, so this looks like the keyboard, not the setting.",
          9,
          25,
          10,
          50
        ),
        act(
          "status",
          "Status changed from In Progress to Resolved. Resolution: Replaced the keyboard on loaner LP-14 and confirmed typing in the facilities log.",
          9,
          25,
          11,
          5
        )
      ]
    }),
    buildTicket({
      id: "TD-2409",
      subject: "Notes to partner groups are bouncing",
      requester: "Nina Okonkwo",
      department: "Membership",
      category: "Email",
      priority: "Medium",
      status: "Waiting on User",
      description:
        "Messages to our partner reading groups come back as undeliverable. It started after I changed my signature. Internal messages go through. I can forward a sample if you tell me where.",
      createdAt: at(9, 26, 8, 33),
      activity: [
        act("opened", "Ticket created.", 9, 26, 8, 33),
        act(
          "reply",
          "Hello Nina,\n\nInternal mail working while partner mail bounces usually points at the recipient address or a signature file, not the whole mailbox.\n\nPlease forward one full bounce, including the address you typed and any error code.\n\nAshmere Press IT",
          9,
          26,
          9,
          10
        ),
        act("status", "Status changed from New to Waiting on User.", 9, 26, 9, 11)
      ]
    }),
    buildTicket({
      id: "TD-2410",
      subject: "Program will not open",
      requester: "Wren Hale",
      department: "Research",
      category: "Software",
      priority: "High",
      status: "In Progress",
      description: "The program will not open and I have a deadline tonight. It just flashes and closes. Please fix it.",
      createdAt: at(10, 1, 6, 58),
      activity: [
        act("opened", "Ticket created.", 10, 1, 6, 58),
        act("status", "Status changed from New to In Progress.", 10, 1, 8, 2),
        act(
          "internal",
          "Subject does not name the program. Pausing until Wren sends the application name and whether a window or an error flashes.",
          10,
          1,
          8,
          6
        )
      ]
    })
  ];
}

function makeId(prefix) {
  const rand = Math.random().toString(36).slice(2, 8);
  return `${prefix}-${Date.now().toString(36)}-${rand}`;
}

function normalizeTicket(value) {
  if (!value || typeof value !== "object" || typeof value.id !== "string") return null;
  return {
    ...value,
    department: typeof value.department === "string" ? value.department : "",
    resolutionNote: typeof value.resolutionNote === "string" ? value.resolutionNote : "",
    seeded: Boolean(value.seeded),
    activity: Array.isArray(value.activity) ? value.activity : []
  };
}

function readStorage() {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    storageWarning = "This browser could not read saved tickets. Showing the sample set for this tab only.";
    return null;
  }
}

function writeStorage(tickets) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tickets));
    storageWarning = "";
    return true;
  } catch {
    storageWarning = "The latest change could not be saved in this browser. It will disappear when you close the tab.";
    return false;
  }
}

function load() {
  if (cache) return clone(cache);

  const raw = readStorage();
  if (raw === null) {
    cache = createSeed();
    writeStorage(cache);
    return clone(cache);
  }

  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) throw new Error("expected a list");
    cache = parsed.map(normalizeTicket).filter(Boolean);
    return clone(cache);
  } catch {
    cache = createSeed();
    writeStorage(cache);
    storageWarning = "Saved TinyDesk data could not be read, so the sample tickets were restored.";
    return clone(cache);
  }
}

function commit(tickets) {
  cache = clone(tickets);
  writeStorage(cache);
  return clone(cache);
}

export function getStorageWarning() {
  return storageWarning;
}

export function getTickets() {
  return load().sort((a, b) => {
    const byTime = b.updatedAt.localeCompare(a.updatedAt);
    return byTime || b.id.localeCompare(a.id);
  });
}

export function getTicket(id) {
  return load().find((ticket) => ticket.id === id) || null;
}

export function resetDemoData() {
  return commit(createSeed());
}

function nextTicketId(tickets) {
  let max = 2410;
  for (const ticket of tickets) {
    const match = /^TD-(\d+)$/.exec(ticket.id);
    if (!match) continue;
    const value = Number(match[1]);
    if (value > max) max = value;
  }
  return `TD-${max + 1}`;
}

export function createTicket(input) {
  const requester = String(input.requester || "").trim();
  const subject = String(input.subject || "").trim();
  const description = String(input.description || "").trim();
  const department = String(input.department || "").trim();
  const category = String(input.category || "").trim();
  const missing = [];
  if (!requester) missing.push("Requester name");
  if (!subject) missing.push("Subject");
  if (!description) missing.push("Description");
  if (!CATEGORIES.includes(category)) missing.push("Category");
  if (missing.length) {
    const verb = missing.length === 1 ? "is" : "are";
    return { ok: false, error: `${missing.join(", ")} ${verb} required.` };
  }

  const tickets = load();
  const now = new Date().toISOString();
  const ticket = {
    id: nextTicketId(tickets),
    subject,
    requester,
    department,
    description,
    category,
    priority: "Medium",
    status: "New",
    resolutionNote: "",
    createdAt: now,
    updatedAt: now,
    seeded: false,
    activity: [
      {
        id: makeId("opened"),
        kind: "opened",
        body: "Ticket created.",
        at: now
      }
    ]
  };
  tickets.push(ticket);
  commit(tickets);
  return { ok: true, ticket: clone(ticket) };
}

export function saveTicketFields(id, input) {
  const tickets = load();
  const ticket = tickets.find((item) => item.id === id);
  if (!ticket) return { ok: false, error: "That ticket is no longer in this demo." };

  const category = String(input.category || "");
  const priority = String(input.priority || "");
  const status = String(input.status || "");
  const note = String(input.resolutionNote || "").trim();

  if (!CATEGORIES.includes(category) || !PRIORITIES.includes(priority) || !STATUSES.includes(status)) {
    return { ok: false, error: "Choose a valid category, priority, and status." };
  }
  if (status === "Resolved" && !note) {
    return { ok: false, error: "A resolution note is required when the status is Resolved." };
  }

  const now = new Date().toISOString();
  const entries = [];
  if (ticket.category !== category) {
    entries.push({
      kind: "field",
      body: `Category changed from ${ticket.category} to ${category}.`
    });
  }
  if (ticket.priority !== priority) {
    entries.push({
      kind: "field",
      body: `Priority changed from ${ticket.priority} to ${priority}.`
    });
  }
  if (ticket.status !== status) {
    let body = `Status changed from ${ticket.status} to ${status}.`;
    if (status === "Resolved") body += ` Resolution: ${note}`;
    entries.push({ kind: "status", body });
  } else if (status === "Resolved" && (ticket.resolutionNote || "") !== note) {
    entries.push({ kind: "status", body: "Resolution note updated." });
  }

  if (!entries.length) return { ok: true, unchanged: true, ticket: clone(ticket) };

  for (const entry of entries) {
    ticket.activity.push({
      id: makeId(entry.kind),
      kind: entry.kind,
      body: entry.body,
      at: now
    });
  }
  ticket.category = category;
  ticket.priority = priority;
  ticket.status = status;
  if (status === "Resolved") ticket.resolutionNote = note;
  ticket.updatedAt = now;
  commit(tickets);
  return { ok: true, ticket: clone(ticket) };
}

export function addUpdate(id, input) {
  const tickets = load();
  const ticket = tickets.find((item) => item.id === id);
  if (!ticket) return { ok: false, error: "That ticket is no longer in this demo." };

  const kind = input.kind === "reply" ? "reply" : input.kind === "internal" ? "internal" : "";
  const body = String(input.body || "").trim();
  if (!kind) return { ok: false, error: "Choose an internal note or a reply to the requester." };
  if (!body) return { ok: false, error: "Write a note or reply before saving." };

  const now = new Date().toISOString();
  ticket.activity.push({ id: makeId(kind), kind, body, at: now });
  ticket.updatedAt = now;
  commit(tickets);
  return { ok: true, ticket: clone(ticket) };
}

export function formatTimestamp(iso) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return String(iso || "");
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(date);
}
