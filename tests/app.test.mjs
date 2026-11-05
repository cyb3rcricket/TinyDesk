import assert from "node:assert/strict";
import { test } from "node:test";

const nodes = new Map();
const windowListeners = {};

function makeNode(id = "") {
  const node = {
    id,
    hidden: false,
    textContent: "",
    className: "",
    value: "",
    disabled: false,
    href: "",
    dateTime: "",
    children: [],
    attributes: {},
    listeners: {},
    elements: {},
    append() {},
    replaceChildren() {},
    setAttribute(name, value) {
      this.attributes[name] = String(value);
    },
    removeAttribute(name) {
      delete this.attributes[name];
    },
    getAttribute(name) {
      return Object.prototype.hasOwnProperty.call(this.attributes, name) ? this.attributes[name] : null;
    },
    addEventListener(type, fn) {
      if (!this.listeners[type]) this.listeners[type] = [];
      this.listeners[type].push(fn);
    },
    removeEventListener() {},
    focus() {},
    reset() {},
    closest() {
      return null;
    }
  };
  if (id === "update-form") {
    const kind = makeNode("update-kind");
    kind.value = "internal";
    node.elements["update-kind"] = kind;
  }
  return node;
}

function installDom(hash) {
  nodes.clear();
  globalThis.localStorage = {
    getItem() {
      return null;
    },
    setItem() {},
    removeItem() {},
    clear() {}
  };
  globalThis.location = { hash };
  globalThis.fetch = async () => ({
    ok: true,
    json: async () => ({
      provider: "ollama",
      placement: "local",
      sendsTicketToProvider: false
    })
  });
  globalThis.window = {
    addEventListener(type, fn) {
      windowListeners[type] = fn;
    },
    removeEventListener() {}
  };
  globalThis.document = {
    title: "",
    activeElement: null,
    addEventListener() {},
    getElementById(id) {
      if (!nodes.has(id)) nodes.set(id, makeNode(id));
      return nodes.get(id);
    },
    createElement() {
      return makeNode();
    }
  };
}

test("a malformed ticket hash shows the queue", async () => {
  installDom("#/ticket/%");
  await import(new URL("../js/app.js", import.meta.url).href);
  assert.equal(document.title, "Ticket queue · TinyDesk");
  assert.equal(nodes.get("view-queue").hidden, false);
  assert.equal(nodes.get("view-ticket").hidden, true);

  location.hash = "#/ticket/TD-2408";
  windowListeners.hashchange();
  assert.equal(document.title, "TD-2408 · TinyDesk");
  assert.equal(nodes.get("view-ticket").hidden, false);

  location.hash = "#/ticket/%ZZ";
  windowListeners.hashchange();
  assert.equal(document.title, "Ticket queue · TinyDesk");
  assert.equal(nodes.get("view-queue").hidden, false);
  assert.equal(nodes.get("view-ticket").hidden, true);
});
