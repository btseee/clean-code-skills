from django.db import models


class Order(models.Model):
    STATUS_CHOICES = [("placed", "Placed"), ("cancelled", "Cancelled")]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="placed")
    total_cents = models.IntegerField()
    payment_reference = models.CharField(max_length=64)

    def __str__(self):
        return f"Order {self.pk} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    sku = models.CharField(max_length=64)
    quantity = models.IntegerField()
