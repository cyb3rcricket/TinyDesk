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

const STORAGE_ERROR =
  "The latest change could not be saved in this browser. It will disappear when you close the tab.";

test("ticket page routing and storage warnings", async (t) => {
  installDom("#/ticket/%");
  await import(new URL("../js/app.js", import.meta.url).href);

  await t.test("a malformed ticket hash shows the queue", () => {
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

  await t.test("a failed save shows an error and the warning stays on later routes", () => {
    const data = new Map();
    globalThis.localStorage = {
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

    location.hash = "#/ticket/TD-2401";
    windowListeners.hashchange();
    assert.equal(document.title, "TD-2401 · TinyDesk");
    nodes.get("field-priority").value = "Low";
    globalThis.localStorage.setItem = () => {
      throw new Error("quota");
    };

    nodes.get("fields-form").listeners.submit[0]({ preventDefault() {} });
    assert.equal(nodes.get("save-status").textContent, STORAGE_ERROR);
    assert.equal(nodes.get("save-status").className.includes("is-error"), true);

    location.hash = "#/";
    windowListeners.hashchange();
    assert.equal(nodes.get("app-banner").hidden, false);
    assert.equal(nodes.get("app-banner").textContent, STORAGE_ERROR);

    location.hash = "#/new";
    windowListeners.hashchange();
    assert.equal(nodes.get("app-banner").hidden, false);
    assert.equal(nodes.get("app-banner").textContent, STORAGE_ERROR);
  });
});
