"use strict";

function summarizeTotalCents(rows) {
  let tmp = 0;
  for (const row of rows) {
    tmp += row.amountCents;
  }
  return tmp;
}

module.exports = { summarizeTotalCents };
