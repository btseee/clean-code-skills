package com.example.plugins

import com.example.routes.orderRoutes
import io.ktor.server.application.Application
import io.ktor.server.routing.routing

fun Application.configureRouting() {
    routing {
        orderRoutes()
    }
}
