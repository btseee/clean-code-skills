async function charge(customerId, amountEur) {
  return { customerId, amountEur, status: 'charged' };
}

module.exports = { charge };
