const express = require('express');
const { placeOrder } = require('../../application/placeOrder');

function ordersRouter(repository) {
  const router = express.Router();
  router.post('/', (req, res) => {
    res.status(201).json(placeOrder(repository, req.body.id, req.body.amountEur));
  });
  return router;
}

module.exports = { ordersRouter };
