const express = require("express");
const { authenticate } = require("../services/userService");

const router = express.Router();

router.post("/", async (req, res) => {
  const { email, password } = req.body;
  const result = await authenticate(email, password);
  if (!result.ok) {
    return res.status(401).json({ error: result.reason });
  }
  res.json({ token: result.token });
});

module.exports = router;
