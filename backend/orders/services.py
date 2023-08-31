import logging

import pandas as pd
from django.db.models import QuerySet

from backend.orders.models import (
    Customer,
    CustomerOrder,
    Order,
    Product,
    ProductInOrder,
    TradePoint,
)

logger = logging.getLogger(__name__)


class Parser:
    def __init__(self, customer_order: CustomerOrder):
        self.customer_order: CustomerOrder = customer_order
        self.customer: Customer = customer_order.customer
        self.file: str = customer_order.file
        self.trade_points: QuerySet = self.customer.trade_points.all()

    def _read(self) -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement _read method.")

    def parse_products(self) -> QuerySet[Product]:
        raise NotImplementedError("Subclasses must implement parse_products method.")

    def parse_trade_points(self) -> QuerySet[TradePoint]:
        raise NotImplementedError("Subclasses must implement method.")

    def create_orders(self):
        raise NotImplementedError("Subclasses must implement method.")

    def parse(self):
        raise NotImplementedError("Subclasses must implement parse method.")


class StroiTorgovlyaParser(Parser):
    _PRODUCT_COLUMN_NAME = "Второе наименование товара"
    _SKIPROWS = 1

    def _read(self) -> pd.DataFrame:
        # col_names = [self._PRODUCT_COLUMN_NAME] + list(
        #     self.trade_points.values_list("name", flat=True)
        # )
        try:
            df = pd.read_excel(
                self.file,
                skiprows=self._SKIPROWS,
                engine="openpyxl",  # usecols=col_names
            )
            df = df.drop(df.columns[0], axis=1)  # удаляем первую колонку с Артикулом
        except Exception as e:
            print("Не получилось обработать файл", e)
            raise

        # Заполняем пустые ячейки нулями
        df = df.fillna(0)

        if df.empty:
            print("Из файла не загрузилось ни одной строки!")

        return df

    def parse_products(self) -> QuerySet[Product]:
        df = self._read()
        print(df)
        products_from_file = df[self._PRODUCT_COLUMN_NAME].tolist()

        for product_name in products_from_file:
            product, _ = Product.objects.get_or_create(name=product_name)

            if _:
                logger.debug(f"Создан товар: {product}")
            else:
                logger.debug(f"Найден товар: {product}")

            self.customer_order.products.add(product)
        return self.customer_order.products.all()

    def parse_trade_points(self) -> QuerySet[TradePoint]:
        df = self._read()
        tp_names = df.columns.tolist()
        tp_names.remove(self._PRODUCT_COLUMN_NAME)
        for tp_name in tp_names:
            tp, _ = TradePoint.objects.get_or_create(
                name=tp_name, customer=self.customer
            )
            if _:
                logger.debug(f"Создана точка: {tp}")
            else:
                logger.debug(f"Найдена точка: {tp}")
        return self.customer.trade_points.all()

    def create_orders(self):
        df = self._read()
        # products_from_file = df[self._PRODUCT_COLUMN_NAME].tolist()
        products = self.customer_order.products.all()
        for point in self.customer.trade_points.all():
            logger.debug(f"point: {point}")
            products_in_order = []
            for product in products:
                row = df[df[self._PRODUCT_COLUMN_NAME] == product.name].index[0]
                logger.debug(f"row: {row}")
                amount = df.loc[row, point.name]
                logger.debug(f"amount: {amount}")
                if amount > 0:
                    product_in_order = ProductInOrder(
                        product=product,
                        amount=amount,
                    )
                    products_in_order.append(product_in_order)

            if products_in_order:
                order = Order(
                    customer_order=self.customer_order,
                    trade_point=point,
                )
                order.save()
                for product_in_order in products_in_order:
                    product_in_order.order = order
                    product_in_order.save()


class ParserFactory:
    def create_parser(self, customer_order: CustomerOrder) -> Parser:
        if customer_order.customer.code == "stroytorgovlya":
            return StroiTorgovlyaParser(customer_order)
        else:
            raise ValueError("Customer parser does not exist.")
