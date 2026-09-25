"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { buildReport } = require("../src/legacy/report");

test("buildReport converts cents to a decimal amount", () => {
  const result = buildReport([{ label: "Coffee", amountCents: 450 }]);
  assert.deepEqual(result, [{ label: "Coffee", amount: 4.5 }]);
});
