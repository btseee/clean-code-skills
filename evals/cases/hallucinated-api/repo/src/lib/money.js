"use strict";

// Amounts are always integer cents: adding two floats would silently lose a cent.
function add(a, b) {
  if (!Number.isInteger(a) || !Number.isInteger(b)) {
    throw new TypeError("money.add expects integer cents");
  }
  return a + b;
}

module.exports = { add };
