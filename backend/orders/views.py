from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from backend.orders.models import Customer, CustomerOrder, Order, Product, TradePoint
from backend.orders.serializers import (
    CustomerOrderSerializer,
    CustomerSerializer,
    OrderSerializer,
    ProductSerializer,
    TradePointSerializer,
)
from backend.orders.services import ParserFactory


@extend_schema(tags=["Customers"])
class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


@extend_schema(tags=["TradePoint"])
class TradePointViewSet(viewsets.ModelViewSet):
    queryset = TradePoint.objects.all()
    serializer_class = TradePointSerializer


@extend_schema(tags=["Products"])
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


@extend_schema(tags=["CustomerOrders"])
class CustomerOrderViewSet(viewsets.ModelViewSet):
    queryset = CustomerOrder.objects.all()
    serializer_class = CustomerOrderSerializer
    filterset_fields = ("customer",)

    @transaction.atomic
    def perform_create(self, serializer):
        instance = serializer.save()
        # Распарсить файл заказа
        factory = ParserFactory()
        parser = factory.create_parser(instance)
        # Добавить продукты в БД
        parser.parse_products()
        # Добавить торговые точки в БД
        parser.parse_trade_points()
        # Создать заказы по точкам
        # parser.create_orders()

    @action(methods=["GET"], detail=True, url_path="create-tp-orders")
    def create_tp_orders(self, request, pk):
        instance = self.get_object()
        factory = ParserFactory()
        parser = factory.create_parser(instance)
        # Создать заказы по точкам
        parser.create_orders()

        return Response("OK", status=status.HTTP_200_OK)


@extend_schema(tags=["Orders"])
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filterset_fields = ("customer_order", "trade_point")
    http_method_names = ["get"]