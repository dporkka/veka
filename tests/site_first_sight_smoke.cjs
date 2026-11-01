"use strict";
// Dependency-free DOM harness for the existing offline browser study page.
// This is NOT a substitute for real-browser accessibility or timing tests.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const html = fs.readFileSync(path.join(__dirname, "../site/cognate-study.html"), "utf8");
const match = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(match, "embedded study script must exist");

async function exercise(schema, prefix, idLen, trials, participantId="VKA101") {
  const nodes = new Map();
  function get(id) {
    if (!nodes.has(id)) {
      nodes.set(id, {
        textContent: "", value: "", checked: false, disabled: false,
        hidden: ["setup", "trial-panel", "complete"].includes(id) && id !== "setup",
        listeners: {}, addEventListener(name, callback) { this.listeners[name] = callback; },
        focus() {}
      });
    }
    return nodes.get(id);
  }
  let downloaded = "";
  let clicked = false;
  const document = {
    getElementById: get,
    addEventListener() {},
    hidden: false,
    body: { append() {} },
    createElement(name) {
      assert.equal(name, "a");
      return {
        download: "", href: "",
        click() { clicked = true; },
        remove() {}
      };
    },
  };
  const window = { addEventListener() {} };
  let time = 1000;
  const context = {
    document, window,
    performance: { now() { time += 105; return time; } },
    Blob: class {
      constructor(parts) { downloaded = parts.join(""); }
    },
    URL: { createObjectURL: () => "blob:test", revokeObjectURL() {} },
    setTimeout: callback => callback(),
    console
  };
  // Expose only the pure session guard in the test sandbox.
  const js = match[1].replace("  function ready(){",
    "  window.__validSession = validSession;\n  function ready(){");
  assert.notEqual(js, match[1], "validator insertion point must exist");
  vm.runInNewContext(js, context);
  const session = {
    schema_version: schema, participant_id: participantId,
    trials: Array.from({length: trials}, (_, i) => ({
      trial_id: prefix + i.toString(16).padStart(idLen, "0"),
      presented_form: "mi",
    }))
  };
  assert.equal(window.__validSession(session), true);
  assert.equal(window.__validSession({...session, target_gloss: "SECRET"}), false);
  assert.equal(window.__validSession({...session, trials: session.trials.slice(1)}), false);
  assert.equal(window.__validSession({...session, trials: [...session.trials.slice(1), session.trials[1]]}), false);
  assert.equal(window.__validSession({...session, schema_version: "unexpected"}), false);

  const source = get("session-file");
  source.files = [{size: 1200, text: async () => JSON.stringify(session)}];
  await source.listeners.change({target: source});
  get("first-language").value = "Swahili";
  get("consent").checked = true;
  get("first-language").listeners.input();
  get("consent").listeners.change();
  assert.equal(get("begin").disabled, false);
  get("begin").listeners.click();
  for (let i=0; i<trials; i++) {
    assert.equal(get("progress").textContent, "Trial "+(i+1)+" of "+trials);
    get("response").value = "don't know";
    get("exposure").value = "no";
    get("trial-form").listeners.submit({preventDefault(){}});
  }
  assert.equal(get("complete").hidden, false);
  assert.equal(get("completion-count").textContent, trials+" unscored responses recorded locally");
  get("export-responses").listeners.click();
  assert.equal(clicked, true);
  assert.ok(downloaded.includes("language_background_family"));
  assert.equal(downloaded.split("\r\n").filter(Boolean).length, trials+1);
  assert.ok(!downloaded.includes("target_gloss"));
  assert.ok(!downloaded.includes("condition"));
  if (participantId.startsWith("-")) {
    assert.ok(downloaded.includes('"' + "'" + participantId + '"'),
              "CSV should neutralize a negative-prefix participant ID");
  }
  console.log(schema + ": validated, completed, exported "+trials+" blinded trials");
}

(async () => {
  await exercise("veka.cognate-session.v07", "C07-", 16, 18);
  await exercise("veka.international-session.v10", "V04-", 12, 24);
  await exercise("veka.international-session.v10", "V04-", 12, 24, "-VKA101");
})().catch(err => { console.error(err); process.exitCode=1; });
