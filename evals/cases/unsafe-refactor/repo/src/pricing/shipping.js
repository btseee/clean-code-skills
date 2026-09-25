"use strict";

function shippingFeeCents(orderTotalCents, isMember, destination) {
  if (destination === "domestic") {
    if (orderTotalCents >= 5000) {
      if (isMember) {
        return 0;
      } else {
        return 500;
      }
    } else {
      if (isMember) {
        return 300;
      } else {
        return 800;
      }
    }
  } else {
    if (orderTotalCents >= 10000) {
      return 1200;
    } else {
      return 2500;
    }
  }
}

module.exports = { shippingFeeCents };
