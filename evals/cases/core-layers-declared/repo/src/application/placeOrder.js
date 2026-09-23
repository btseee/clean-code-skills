const { Order } = require('../domain/order');

function placeOrder(repository, id, amountEur) {
  const order = new Order(id, amountEur);
  repository.save(order);
  return order;
}

module.exports = { placeOrder };
