from django.contrib import admin

from backend.orders.models import Customer, CustomerOrder, Order, Product, TradePoint


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "id")


@admin.register(TradePoint)
class TradePointAdmin(admin.ModelAdmin):
    pass


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor_code", "amount_in_pack", "id")
    list_editable = (
        "vendor_code",
        "amount_in_pack",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass


@admin.register(CustomerOrder)
class CustomerOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "file")
