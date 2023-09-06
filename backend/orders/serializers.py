from rest_framework import serializers

from backend.orders.models import (
    Customer,
    CustomerOrder,
    CustomerProduct,
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
            "order_in_packs",
        ]


class TradePointSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradePoint
        fields = [
            "id",
            "name",
            "customer",
            "sapcode",
        ]


class ProductSerializer(serializers.ModelSerializer):
    option = serializers.SerializerMethodField(read_only=True)

    def get_option(self, obj):
        return f"({obj.vendor_code}) {obj.name}"

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "vendor_code",
            "volume",
            "amount_in_pack",
            "option",
        ]


class CustomerProductSerializer(serializers.ModelSerializer):
    base_product = ProductSerializer(read_only=True)
    base_product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source="base_product",
        write_only=True,
    )

    class Meta:
        model = CustomerProduct
        fields = [
            "id",
            "name",
            "vendor_code",
            "base_product",
            "base_product_id",
        ]
        extra_kwargs = {
            "name": {"read_only": True},
            "vendor_code": {"read_only": True},
        }


class ProductInOrderSerializer(serializers.ModelSerializer):
    vendor_code = serializers.ReadOnlyField(source="product.vendor_code")
    base_vendor_code = serializers.ReadOnlyField(
        source="product.base_product.vendor_code", default=""
    )
    product_name = serializers.ReadOnlyField(source="product.name")
    base_product_name = serializers.ReadOnlyField(
        source="product.base_product.name", default=""
    )
    amount = serializers.IntegerField()
    amount_in_pack = serializers.ReadOnlyField(
        source="product.base_product.amount_in_pack", default=0
    )

    class Meta:
        model = ProductInOrder
        fields = [
            "id",
            "product_name",
            "base_product_name",
            "vendor_code",
            "base_vendor_code",
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
    products = CustomerProductSerializer(many=True, read_only=True)
    created = serializers.DateTimeField(format="%d.%m.%Y", read_only=True)
    order_in_packs = serializers.BooleanField(
        read_only=True, source="customer.order_in_packs"
    )

    class Meta:
        model = CustomerOrder
        fields = [
            "id",
            "customer",
            "customer_name",
            "file",
            "order_in_packs",
            "products",
            "created",
        ]
