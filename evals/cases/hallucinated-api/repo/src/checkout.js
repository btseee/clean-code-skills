"use strict";

const money = require("./lib/money");

// Every amount here is already a line total in cents; combining them is the
// only place the checkout adds money to money.
function subtotal(lineAmountsCents) {
  return lineAmountsCents.reduce((total, amount) => money.add(total, amount), 0);
}

module.exports = { subtotal };
