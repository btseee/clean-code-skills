import { test } from "node:test";
import assert from "node:assert/strict";
import { isDue } from "./subscription";

test("a subscription renewing yesterday is due", () => {
  const yesterday = new Date(Date.now() - 86_400_000);
  assert.equal(isDue({ renewsAt: yesterday }), true);
});

test("a subscription renewing at exactly the current instant is due", () => {
  // Flaky today: the domain reads the real clock, so 'now' has moved on by the time isDue runs.
  const now = new Date();
  assert.equal(isDue({ renewsAt: now }), true);
});
