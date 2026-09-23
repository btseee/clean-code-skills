const express = require('express');
const orders = require('./routes/orders');

const app = express();
app.use(express.json());
app.use('/orders', orders);

module.exports = app;
