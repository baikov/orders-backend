from django.db import transaction

# from django.db.models.query import QuerySet
from drf_spectacular.utils import extend_schema

# from loguru import logger as log
from rest_framework import filters, viewsets  # status

# from rest_framework.permissions import IsAuthenticated
from backend.orders.models import (
    Customer,
    CustomerOrder,
    CustomerProduct,
    Order,
    Product,
    TradePoint,
)
from backend.orders.serializers import (
    CustomerOrderSerializer,
    CustomerProductSerializer,
    CustomerSerializer,
    OrderSerializer,
    ProductSerializer,
    TradePointSerializer,
)
from backend.orders.services import ParserFactory

# from backend.orders.tasks import create_customer_order_task


@extend_schema(tags=["Customers"])
class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    # permission_classes = [IsAuthenticated]

    # def get_queryset(self) -> QuerySet:
    #     user = self.request.user
    #     log.debug("user: {}", user)
    #     if user.is_anonymous:
    #         return Customer.objects.none()
    #     if user.is_superuser:
    #         return super().get_queryset()
    #     return super().get_queryset().filter(owner=user)


@extend_schema(tags=["TradePoint"])
class TradePointViewSet(viewsets.ModelViewSet):
    queryset = TradePoint.objects.all()
    serializer_class = TradePointSerializer
    filterset_fields = ("customer",)
    # permission_classes = [IsAuthenticated]

    # def get_queryset(self) -> QuerySet:
    #     user = self.request.user
    #     if user.is_anonymous:
    #         return TradePoint.objects.none()
    #     if user.is_superuser:
    #         return super().get_queryset()
    #     return super().get_queryset().filter(customer__owner=user)


@extend_schema(tags=["Products"])
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["vendor_code"]
    # permission_classes = (IsAuthenticated,)


@extend_schema(tags=["CustomerProducts"])
class CustomerProductViewSet(viewsets.ModelViewSet):
    queryset = CustomerProduct.objects.all()
    serializer_class = CustomerProductSerializer
    # permission_classes = [IsAuthenticated]

    # def get_queryset(self) -> QuerySet:
    #     user = self.request.user
    #     if user.is_anonymous:
    #         return CustomerProduct.objects.none()
    #     if user.is_superuser:
    #         return super().get_queryset()
    #     return super().get_queryset().filter(customer__owner=user)


@extend_schema(tags=["CustomerOrders"])
class CustomerOrderViewSet(viewsets.ModelViewSet):
    queryset = CustomerOrder.objects.prefetch_related("products", "products__base_product").order_by("-created")
    serializer_class = CustomerOrderSerializer
    filterset_fields = ("customer",)
    # permission_classes = [IsAuthenticated]

    # def get_queryset(self) -> QuerySet:
    #     user = self.request.user
    #     if user.is_anonymous:
    #         return CustomerOrder.objects.none()
    #     if user.is_superuser:
    #         return super().get_queryset()
    #     return super().get_queryset().filter(customer__owner=user)

    @transaction.atomic
    def perform_create(self, serializer):
        instance = serializer.save()
        # Распарсить файл заказа
        factory = ParserFactory()
        parser = factory.create_parser(instance.customer.code)(instance)
        parser.parse()
        # Распарсить файл заказа в таске
        # task_id = create_customer_order_task.delay(instance.pk)
        # log.info("task_id: {}", task_id)


@extend_schema(tags=["Orders"])
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filterset_fields = ("customer_order", "trade_point")
    http_method_names = ["get"]
    # permission_classes = [IsAuthenticated]

    # def get_queryset(self) -> QuerySet:
    #     user = self.request.user
    #     if user.is_anonymous:
    #         return Order.objects.none()
    #     if user.is_superuser:
    #         return super().get_queryset()
    #     return super().get_queryset().filter(customer_order__customer__owner=user)
