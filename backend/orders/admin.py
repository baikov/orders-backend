from django.contrib import admin

from backend.orders.models import (
    Customer,
    CustomerOrder,
    CustomerProduct,
    Order,
    Product,
    TradePoint,
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "id")


@admin.register(TradePoint)
class TradePointAdmin(admin.ModelAdmin):
    list_display = ("name", "customer", "sapcode", "id")
    list_editable = (
        "sapcode",
        "customer",
    )
    list_filter = ("customer",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor_code", "amount_in_pack", "id")
    list_editable = (
        "vendor_code",
        "amount_in_pack",
    )


@admin.register(CustomerProduct)
class CustomerProductAdmin(admin.ModelAdmin):
    list_display = ("name", "customer", "vendor_code", "id")
    list_editable = ("customer",)
    list_filter = ("customer",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_order", "trade_point")
    list_filter = ("customer_order", "trade_point")


@admin.register(CustomerOrder)
class CustomerOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "file", "created")
    list_filter = ("customer",)
