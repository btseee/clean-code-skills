package main

import (
	"log"

	"github.com/gin-gonic/gin"

	"example.com/orders/internal/handler"
)

func main() {
	r := gin.Default()
	r.POST("/orders", handler.CreateOrder)
	log.Fatal(r.Run(":8080"))
}
