package com.example.service

import com.example.model.Order

class OrderService {
    private val orders = mutableListOf(
        Order(id = 1, item = "Desk", quantity = 2),
    )

    fun listOrders(): List<Order> = orders.toList()
}
