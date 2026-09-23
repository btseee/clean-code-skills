package com.example.orders.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import com.example.orders.data.OrderRepository
import com.example.orders.model.Order

@Composable
fun OrdersScreen(repository: OrderRepository = OrderRepository()) {
    var orders by remember { mutableStateOf<List<Order>>(emptyList()) }

    LaunchedEffect(Unit) {
        orders = repository.getOrders()
    }

    Column {
        orders.forEach { order ->
            Text("${order.item} x${order.quantity}")
        }
    }
}
