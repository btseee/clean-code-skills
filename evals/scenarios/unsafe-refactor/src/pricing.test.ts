import { test } from "node:test";
import assert from "node:assert/strict";
import { applyDiscount } from "./pricing";

test("15% off 119.99 is 101.99", () => {
  assert.equal(applyDiscount(11999, 15), 10199);
});

test("10% off 29.99 is 26.99", () => {
  assert.equal(applyDiscount(2999, 10), 2699);
});
