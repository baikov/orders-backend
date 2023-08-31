from datetime import datetime
from functools import partial

from django.db import models
from django_extensions.db.models import AutoSlugField
from slugify import slugify


def get_order_file_path(instance, filename):
    today = datetime.now().astimezone().date()
    path = f"orders/customer-{instance.customer.id}/"
    path += f"/{today.strftime('%d-%m-%Y')}_{filename}"
    return path


class Customer(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название клиента")
    code = AutoSlugField(
        verbose_name="Уникальный код клиента",
        editable=True,
        blank=False,
        populate_from="name",
        slugify_function=partial(slugify, replacements=[["я", "ya"], ["/", ""]]),
        max_length=30,
    )

    class Meta:
        ordering = ("id",)
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        db_table = "customers"

    def __str__(self):
        return self.name


class TradePoint(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название торговой точки")
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        verbose_name="Клиент",
        related_name="trade_points",
    )
    sapcode = models.CharField(max_length=255, blank=True, verbose_name="SAP код")

    class Meta:
        ordering = ("id",)
        verbose_name = "Торговая точка"
        verbose_name_plural = "Торговые точки"
        db_table = "trade_points"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название товара")
    vendor_code = models.CharField(max_length=255, blank=True, verbose_name="Артикул")
    amount_in_pack = models.PositiveIntegerField(
        verbose_name="Количество в упаковке", blank=True, null=True
    )

    class Meta:
        ordering = ("id",)
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        db_table = "products"

    def __str__(self):
        return self.name


class CustomerOrder(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, verbose_name="Клиент", related_name="orders"
    )
    file = models.FileField(upload_to=get_order_file_path, verbose_name="Файл")
    products = models.ManyToManyField(
        Product, related_name="customer_orders", verbose_name="Товары в заказе"
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    modified = models.DateTimeField(auto_now=True, verbose_name="Изменено")

    class Meta:
        ordering = ("id",)
        verbose_name = "Общий заказ"
        verbose_name_plural = "Общие заказы"
        db_table = "customer_orders"


class Order(models.Model):
    customer_order = models.ForeignKey(
        CustomerOrder,
        on_delete=models.CASCADE,
        verbose_name="Общий заказ",
        related_name="tp_orders",
    )
    trade_point = models.ForeignKey(
        TradePoint,
        on_delete=models.CASCADE,
        verbose_name="Торговая точка",
        related_name="orders",
    )
    products = models.ManyToManyField(
        Product,
        related_name="orders",
        through="ProductInOrder",
        verbose_name="Товары в заказе",
    )

    class Meta:
        ordering = ("id",)
        verbose_name = "Заказ на торговую точку"
        verbose_name_plural = "Заказы на торговые точки"
        db_table = "orders"

    def __str__(self):
        return self.trade_point.name


class ProductInOrder(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()

    class Meta:
        ordering = ("id",)
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказах"
        db_table = "products_in_orders"
