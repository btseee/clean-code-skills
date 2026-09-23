package com.example.model

import kotlinx.serialization.Serializable

@Serializable
data class Order(
    val id: Int,
    val item: String,
    val quantity: Int,
)
