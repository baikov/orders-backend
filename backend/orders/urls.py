from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from backend.orders.views import (
    CustomerOrderViewSet,
    CustomerProductViewSet,
    CustomerViewSet,
    OrderViewSet,
    ProductViewSet,
    TradePointViewSet,
)

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()  # type: ignore

router.register("customers", CustomerViewSet, basename="customers")
router.register("orders", OrderViewSet, basename="orders")
router.register("products", ProductViewSet, basename="products")
router.register(
    "customer-products", CustomerProductViewSet, basename="customer-products"
)
router.register("trade-points", TradePointViewSet, basename="trade-points")
router.register("customer-orders", CustomerOrderViewSet, basename="customer-orders")


app_name = "orders"
urlpatterns = router.urls
