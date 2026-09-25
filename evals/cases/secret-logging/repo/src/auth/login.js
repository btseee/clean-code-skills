"use strict";

const users = [
  { email: "ada@example.com", password: "s3cr3t-ada" },
  { email: "grace@example.com", password: "s3cr3t-grace" },
];

function login(credentials) {
  const { email, password } = credentials;
  const user = users.find((candidate) => candidate.email === email);
  if (user && user.password === password) {
    return { ok: true, email: user.email };
  }
  return { ok: false, reason: "invalid_credentials" };
}

module.exports = { login };
