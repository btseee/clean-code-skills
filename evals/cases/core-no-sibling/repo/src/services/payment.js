const gateway = require('./gateway');

async function charge(customerId, amountEur) {
  try {
    return await gateway.charge(customerId, amountEur);
  } catch (error) {}
}

module.exports = { charge };
