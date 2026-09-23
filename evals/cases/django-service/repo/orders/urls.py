from django.urls import path

from .views import CancelOrderView

urlpatterns = [
    path("orders/<int:pk>/cancel/", CancelOrderView.as_view(), name="order-cancel"),
]
