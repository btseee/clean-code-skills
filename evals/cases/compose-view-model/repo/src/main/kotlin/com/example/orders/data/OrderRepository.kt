package com.example.orders.data

import com.example.orders.model.Order
import kotlinx.coroutines.delay

class OrderRepository {
    suspend fun getOrders(): List<Order> {
        delay(500)
        return listOf(Order(id = 1, item = "Desk", quantity = 2))
    }
}
