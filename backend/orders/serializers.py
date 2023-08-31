from rest_framework import serializers

from backend.orders.models import (
    Customer,
    CustomerOrder,
    Order,
    Product,
    ProductInOrder,
    TradePoint,
)


class CustomerSerializer(serializers.ModelSerializer):
    tp_count = serializers.SerializerMethodField(read_only=True)
    last_order = serializers.SerializerMethodField(read_only=True)

    def get_tp_count(self, obj):
        return obj.trade_points.count()

    def get_last_order(self, obj):
        last_order = obj.orders.order_by("-created").first()

        return CustomerOrderSerializer(last_order).data

    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "tp_count",
            "last_order",
        ]


class TradePointSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradePoint
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class ProductInOrderSerializer(serializers.ModelSerializer):
    vendor_code = serializers.ReadOnlyField(source="product.vendor_code")
    product_name = serializers.ReadOnlyField(source="product.name")
    amount = serializers.IntegerField()
    amount_in_pack = serializers.ReadOnlyField(source="product.amount_in_pack")

    # def get_amount(self, obj):
    #     return int(obj.amount / obj.product.amount_in_pack)
    #     # return obj.amount

    class Meta:
        model = ProductInOrder
        fields = [
            "id",
            "product_name",
            "vendor_code",
            "amount",
            "amount_in_pack",
        ]


class OrderSerializer(serializers.ModelSerializer):
    trade_point_name = serializers.ReadOnlyField(source="trade_point.name")
    trade_point_sapcode = serializers.ReadOnlyField(source="trade_point.sapcode")
    products_list = serializers.SerializerMethodField(read_only=True)

    def get_products_list(self, obj):
        products = ProductInOrder.objects.filter(order=obj)
        return ProductInOrderSerializer(products, many=True).data

    class Meta:
        model = Order
        fields = [
            "id",
            "customer_order",
            "trade_point",
            "trade_point_name",
            "trade_point_sapcode",
            "products_list",
        ]


class CustomerOrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source="customer.name")
    products = ProductSerializer(many=True, read_only=True)
    created = serializers.DateTimeField(format="%d.%m.%Y", read_only=True)

    class Meta:
        model = CustomerOrder
        fields = [
            "id",
            "customer",
            "customer_name",
            "file",
            "products",
            "created",
        ]