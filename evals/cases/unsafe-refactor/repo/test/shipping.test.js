"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { shippingFeeCents } = require("../src/pricing/shipping");

test("domestic orders over the free-shipping threshold ship free for members", () => {
  assert.equal(shippingFeeCents(5000, true, "domestic"), 0);
});

test("domestic orders over the threshold still charge non-members", () => {
  assert.equal(shippingFeeCents(5000, false, "domestic"), 500);
});

test("domestic orders under the threshold charge members a reduced fee", () => {
  assert.equal(shippingFeeCents(4999, true, "domestic"), 300);
});

test("domestic orders under the threshold charge non-members the full fee", () => {
  assert.equal(shippingFeeCents(4999, false, "domestic"), 800);
});

test("international orders over their threshold pay the reduced flat fee", () => {
  assert.equal(shippingFeeCents(10000, true, "international"), 1200);
});

test("international orders under their threshold pay the full flat fee", () => {
  assert.equal(shippingFeeCents(9999, false, "international"), 2500);
});
