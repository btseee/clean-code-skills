const express = require("express");
const loginRoutes = require("./routes/login");

const app = express();

app.use(express.json());
app.use("/login", loginRoutes);

app.use((err, req, res, next) => {
  console.error(err.message);
  res.status(err.status || 500).json({ error: "Something went wrong" });
});

module.exports = app;
