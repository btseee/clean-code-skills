"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { login } = require("../src/auth/login");

test("accepts the correct email and password", () => {
  assert.deepEqual(login({ email: "ada@example.com", password: "s3cr3t-ada" }),
    { ok: true, email: "ada@example.com" });
});

test("rejects the wrong password", () => {
  assert.equal(login({ email: "ada@example.com", password: "wrong" }).ok, false);
});

test("rejects an unknown email", () => {
  assert.equal(login({ email: "nobody@example.com", password: "whatever" }).ok, false);
});
