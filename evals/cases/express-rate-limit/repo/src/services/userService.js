const users = new Map([["ada@example.com", { id: "u1", password: "hunter2" }]]);

async function authenticate(email, password) {
  const user = users.get(email);
  if (!user || user.password !== password) {
    return { ok: false, reason: "invalid credentials" };
  }
  return { ok: true, token: `token-${user.id}` };
}

module.exports = { authenticate };
