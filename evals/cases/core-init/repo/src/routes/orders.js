const express = require('express');
const orderService = require('../services/orderService');

const router = express.Router();

router.get('/', async (req, res) => {
  res.json(await orderService.list());
});

module.exports = router;
