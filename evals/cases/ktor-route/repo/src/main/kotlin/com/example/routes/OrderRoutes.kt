package com.example.routes

import com.example.service.OrderService
import io.ktor.server.application.call
import io.ktor.server.response.respond
import io.ktor.server.routing.Route
import io.ktor.server.routing.get

private val orderService = OrderService()

fun Route.orderRoutes() {
    get("/orders") {
        call.respond(orderService.listOrders())
    }
}
