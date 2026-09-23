from django.http import JsonResponse
from django.views import View

from .models import Order


class CancelOrderView(View):
    def post(self, request, pk):
        order = Order.objects.get(pk=pk)
        order.status = "cancelled"
        order.save(update_fields=["status"])
        return JsonResponse({"status": order.status})
