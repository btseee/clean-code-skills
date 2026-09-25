"use strict";

function buildReport(rows) {
  const tmp = [];
  for (const row of rows) {
    const val = row.amountCents / 100;
    tmp.push({ label: row.label, amount: val });
  }
  return tmp;
}

module.exports = { buildReport };
