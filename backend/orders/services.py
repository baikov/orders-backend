import os
import re
import zipfile
from abc import ABC, abstractmethod
from uuid import uuid4

import pandas as pd
from django.conf import settings
from django.db.models import QuerySet

# from loguru import logger
from backend.orders.models import (
    Customer,
    CustomerOrder,
    CustomerProduct,
    Order,
    ProductInOrder,
    TradePoint,
)


class Parser(ABC):
    def __init__(self, customer_order: CustomerOrder):
        self.customer_order: CustomerOrder = customer_order
        self.customer: Customer = customer_order.customer
        self.file = customer_order.file
        self.trade_points: QuerySet = self.customer.trade_points.all()
        self.file_path = os.path.join(settings.MEDIA_ROOT, self.file.name)

    @abstractmethod
    def _read(self) -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement _read method.")

    @abstractmethod
    def _parse_products(self, df: pd.DataFrame) -> None:
        raise NotImplementedError("Subclasses must implement parse_products method.")

    @abstractmethod
    def _parse_trade_points(self, df: pd.DataFrame) -> list[TradePoint]:
        raise NotImplementedError("Subclasses must implement method.")

    @abstractmethod
    def _create_orders(self, df: pd.DataFrame, tp_list: list[TradePoint]) -> None:
        raise NotImplementedError("Subclasses must implement method.")

    @abstractmethod
    def parse(self):
        raise NotImplementedError("Subclasses must implement parse method.")


class StroiTorgovlyaParser(Parser):
    _PRODUCT_COLUMN_NAME = "Второе наименование товара"
    _CODE_COLUMN_NAME = "Артикул"
    _SKIPROWS = 1

    def _read(self) -> pd.DataFrame:
        try:
            df = pd.read_excel(
                self.file,
                skiprows=self._SKIPROWS,
                engine="openpyxl",
            )
            # df = df.drop(df.columns[0], axis=1)  # удаляем первую колонку с Артикулом
        except Exception as e:
            print("Не получилось обработать файл", e)
            raise

        # Заполняем пустые ячейки нулями
        df = df.fillna(0)

        if df.empty:
            print("Из файла не загрузилось ни одной строки!")

        return df

    def _parse_trade_points(self, df: pd.DataFrame) -> list[TradePoint]:
        tp_list = []
        tp_names = df.columns.tolist()
        tp_names.remove(self._PRODUCT_COLUMN_NAME)
        tp_names.remove(self._CODE_COLUMN_NAME)
        for tp_name in tp_names:
            tp, _ = TradePoint.objects.get_or_create(name=tp_name, customer=self.customer)
            if df[tp.name].tolist():
                tp_list.append(tp)
        return tp_list

    def _parse_products(self, df: pd.DataFrame) -> None:
        products_from_file = df[self._PRODUCT_COLUMN_NAME].tolist()
        codes_from_file = df[self._CODE_COLUMN_NAME].tolist()

        # Create products if not exist
        for row_num in range(len(products_from_file)):
            customer_product, _ = CustomerProduct.objects.get_or_create(
                name=products_from_file[row_num],
                vendor_code=codes_from_file[row_num],
                customer=self.customer,
            )

    def _create_orders(self, df: pd.DataFrame, tp_list: list[TradePoint]) -> None:
        unique_customer_products = []
        for tp in tp_list:
            products_in_order = []

            for _, row in df.iterrows():
                if row[tp.name] > 0:
                    customer_product = CustomerProduct.objects.get(
                        name=row[self._PRODUCT_COLUMN_NAME],
                    )
                    product_in_order = ProductInOrder(
                        product=customer_product,
                        amount=int(row[tp.name]),
                    )
                    products_in_order.append(product_in_order)

                    if customer_product not in unique_customer_products:
                        unique_customer_products.append(customer_product)

            if products_in_order:
                order = Order(
                    customer_order=self.customer_order,
                    trade_point=tp,
                )
                order.save()
                for product_in_order in products_in_order:
                    product_in_order.order = order
                    product_in_order.save()
        self.customer_order.products.add(*unique_customer_products)

    def parse(self):
        df = self._read()

        tp_list = self._parse_trade_points(df)
        self._parse_products(df)
        self._create_orders(df, tp_list)


class OseniParser(Parser):
    _PRODUCT_COLUMN_NAME = "Номенклатура"
    _TP_COLUMN_NAME = "Код"
    _VENDOR_CODE_COLUMN_NAME = "Артикул"
    _QUANTITY_COLUMN_NAME = "Количество"
    _SKIPROWS = 7
    _INCLUDE_COLUMNS = [
        _VENDOR_CODE_COLUMN_NAME,
        _TP_COLUMN_NAME,
        _PRODUCT_COLUMN_NAME,
        _QUANTITY_COLUMN_NAME,
    ]

    def _read(self) -> pd.DataFrame:
        try:
            df = pd.read_excel(
                self.file,
                skiprows=self._SKIPROWS,
                usecols=self._INCLUDE_COLUMNS,
                engine="openpyxl",
            )
        except Exception as e:
            print("Не получилось обработать файл", e)
            raise

        # Заполняем пустые ячейки нулями
        df = df.fillna(0)

        if df.empty:
            print("Из файла не загрузилось ни одной строки!")

        return df

    def parse(self):
        df = self._read()
        order = None
        unique_customer_products = []
        for _, row in df.iterrows():
            if row[self._VENDOR_CODE_COLUMN_NAME] == "Итого":
                break
            if str(row[self._VENDOR_CODE_COLUMN_NAME]) != str(row[self._TP_COLUMN_NAME]):
                tp, _ = TradePoint.objects.get_or_create(name=row[self._TP_COLUMN_NAME], customer=self.customer)
                order = Order(customer_order=self.customer_order, trade_point=tp)
                order.save()

            # TODO: get by unique vendor_code not by name
            elif row[self._TP_COLUMN_NAME] and order is not None:
                customer_product, _ = CustomerProduct.objects.get_or_create(
                    name=row[self._PRODUCT_COLUMN_NAME].strip(),
                    vendor_code=str(row[self._VENDOR_CODE_COLUMN_NAME]).strip(),
                    customer=self.customer,
                )
                if customer_product not in unique_customer_products:
                    unique_customer_products.append(customer_product)

                if int(row[self._QUANTITY_COLUMN_NAME]) > 0:
                    product_in_order = ProductInOrder(
                        product=customer_product,
                        amount=int(row[self._QUANTITY_COLUMN_NAME]),
                        order=order,
                    )
                    product_in_order.save()
        self.customer_order.products.add(*unique_customer_products)


class OseniParserV2(Parser):
    _PRODUCT_COLUMN_NAME = "Номенклатура"
    _TP_COLUMN_NAME = "Магазин"
    _VENDOR_CODE_COLUMN_NAME = "Артикул"
    _QUANTITY_COLUMN_NAME = "Количество"
    _SKIPROWS = 0
    _INCLUDE_COLUMNS = [
        _VENDOR_CODE_COLUMN_NAME,
        _TP_COLUMN_NAME,
        _PRODUCT_COLUMN_NAME,
        _QUANTITY_COLUMN_NAME,
    ]

    def _read(self) -> pd.DataFrame:
        try:
            df = pd.read_excel(
                self.file,
                skiprows=self._SKIPROWS,
                usecols=self._INCLUDE_COLUMNS,
                engine="openpyxl",
            )
        except Exception as e:
            print("Не получилось обработать файл", e)
            raise

        # Заполняем пустые ячейки нулями
        df = df.fillna(0)

        if df.empty:
            print("Из файла не загрузилось ни одной строки!")

        return df

    def _parse_products(self, df):
        pass

    def _create_orders(self, df, tp_list):
        pass

    def _parse_trade_points(self, df):
        pass

    def parse(self):
        df = self._read()
        order = None
        unique_customer_products = []
        tp_name = None
        for _, row in df.iterrows():
            if row[self._PRODUCT_COLUMN_NAME] == "Итого:":
                break

            if tp_name != row[self._TP_COLUMN_NAME]:
                tp_name = row[self._TP_COLUMN_NAME]
                tp, _ = TradePoint.objects.get_or_create(name=row[self._TP_COLUMN_NAME], customer=self.customer)
                order = Order(customer_order=self.customer_order, trade_point=tp)
                order.save()

            customer_product, _ = CustomerProduct.objects.get_or_create(
                name=row[self._PRODUCT_COLUMN_NAME].strip(),
                vendor_code=str(int(row[self._VENDOR_CODE_COLUMN_NAME])).strip(),
                customer=self.customer,
            )
            if customer_product not in unique_customer_products:
                unique_customer_products.append(customer_product)

            if int(row[self._QUANTITY_COLUMN_NAME]) > 0:
                product_in_order = ProductInOrder(
                    product=customer_product,
                    amount=int(row[self._QUANTITY_COLUMN_NAME]),
                    order=order,
                )
                product_in_order.save()
        self.customer_order.products.add(*unique_customer_products)


class KruasanParser(Parser):
    _PRODUCT_COLUMN_NAME = "Напитки"
    _SKIPROWS = 0

    def _read(self) -> pd.DataFrame:
        try:
            df = pd.read_excel(
                self.file,
                header=None,
                skiprows=self._SKIPROWS,
                engine="openpyxl",
            )
        except Exception as e:
            print("Не получилось обработать файл", e)
            raise

        # Заполняем пустые ячейки нулями
        df = df.fillna(0)

        if df.empty:
            print("Из файла не загрузилось ни одной строки!")

        return df

    def _parse_trade_points(self, df: pd.DataFrame) -> list[TradePoint]:
        # Удаляем первый столбец (столбец 'A')
        tp_df = df.iloc[:, 1:]
        # Оставляем только первые три строки
        tp_df = tp_df.head(3)
        tp_list = []
        for column_name in tp_df.columns:
            column_data = tp_df[column_name].tolist()
            tp_name = f"{column_data[1]} ({column_data[0]})"
            tp, _ = TradePoint.objects.get_or_create(
                sapcode=column_data[2],
                customer=self.customer,
                defaults={"name": tp_name},
            )

            tp_list.append(tp)

        return tp_list

    def _parse_products(self, df: pd.DataFrame) -> None:
        # Удаляем вторую и третью строки (индексы 1 и 2)
        prod_df = df.drop([0, 1, 2])
        products_from_file = prod_df[0].tolist()
        # Create products if not exist
        for row_num in range(len(products_from_file)):
            CustomerProduct.objects.get_or_create(
                name=products_from_file[row_num].strip(),
                customer=self.customer,
                defaults={"vendor_code": uuid4().hex},
            )

    def _create_orders(self, df: pd.DataFrame, tp_list: list[TradePoint]) -> None:
        rename = {}
        for column_name in df.columns:
            values = df[column_name].tolist()
            if column_name == 0:
                rename[column_name] = values[0]
                self._PRODUCT_COLUMN_NAME = values[0]
            else:
                rename[column_name] = values[2]
        df = df.rename(columns=rename)
        df = df.drop([0, 1, 2])
        unique_customer_products = []
        for tp in tp_list:
            products_in_order = []

            for _, row in df.iterrows():
                if row[tp.sapcode] > 0:
                    customer_product = CustomerProduct.objects.get(
                        name=row[self._PRODUCT_COLUMN_NAME],
                    )
                    product_in_order = ProductInOrder(
                        product=customer_product,
                        amount=int(row[tp.sapcode]),
                    )
                    products_in_order.append(product_in_order)

                    if customer_product not in unique_customer_products:
                        unique_customer_products.append(customer_product)

            if products_in_order:
                order = Order(
                    customer_order=self.customer_order,
                    trade_point=tp,
                )
                order.save()
                for product_in_order in products_in_order:
                    product_in_order.order = order
                    product_in_order.save()
        self.customer_order.products.add(*unique_customer_products)

    def parse(self):
        df = self._read()
        tp_list = self._parse_trade_points(df)
        self._parse_products(df)
        self._create_orders(df, tp_list)


class BahusParser(Parser):
    _PRODUCT_COLUMN_NAME = "Товар"
    _VENDOR_CODE_COLUMN_NAME = "Артикул"
    _QUANTITY_COLUMN_NAME = "Кол-во"
    _SKIPROWS = 6
    _INCLUDE_COLUMNS = [
        _VENDOR_CODE_COLUMN_NAME,
        _PRODUCT_COLUMN_NAME,
        _QUANTITY_COLUMN_NAME,
    ]

    def _read(self) -> list[pd.DataFrame]:
        file_size = os.path.getsize(self.file_path)
        if file_size > 50 * 1024 * 1024:  # 50 MB
            raise Exception("Файл больше 50 МБ.")
        if not zipfile.is_zipfile(self.file_path):
            raise Exception("Файл не является ZIP-архивом.")
        try:
            with zipfile.ZipFile(self.file_path, "r") as z:
                xlsx_files = [f for f in z.namelist() if f.endswith(".xlsx")]
                dataframes = [pd.read_excel(z.open(file), header=None, engine="openpyxl") for file in xlsx_files]
        except zipfile.BadZipFile:
            print("Файл повреждён или не является правильным ZIP-архивом.")
        for df in dataframes:
            continue
            # logger.debug("Заказчик: {}", df.iat[3, 3])
        # logger.debug("Адрес: {}", dataframes[0].iat[4, 3])

        return dataframes

    def _parse_trade_points(self, dfs: list[pd.DataFrame]) -> list[TradePoint]:
        unique_customer_products = []
        # logger.debug("DFS: {}", dfs)
        for df in dfs:
            df = df.fillna(0)
            match = re.search(r"\".*\"", df.iat[3, 3])
            if match:
                tp_name = match.group(0)[1:-1]
            else:
                tp_name = df.iat[3, 3]
            # logger.info("Заказчик: {}", tp_name)
            # logger.info("Адрес: {}", df.iat[4, 3])

            # Create TP
            tp, _ = TradePoint.objects.get_or_create(name=tp_name, customer=self.customer)
            # Create Order
            order = Order(customer_order=self.customer_order, trade_point=tp)
            order.save()

            df.drop([0, 1, 2, 3, 4, 5], inplace=True)

            df.columns = df.iloc[0]
            df.drop(df.index[0], inplace=True)

            df = df.loc[:, self._INCLUDE_COLUMNS]
            # logger.debug(df)

            for _, row in df.iterrows():
                # logger.debug(f"Artice: {row[self._VENDOR_CODE_COLUMN_NAME]}")
                if not row[self._VENDOR_CODE_COLUMN_NAME]:
                    break
                customer_product, _ = CustomerProduct.objects.get_or_create(
                    name=str(row[self._PRODUCT_COLUMN_NAME]).strip(),
                    vendor_code=str(row[self._VENDOR_CODE_COLUMN_NAME]).strip(),
                    customer=self.customer,
                )
                if customer_product not in unique_customer_products:
                    unique_customer_products.append(customer_product)

                if int(row[self._QUANTITY_COLUMN_NAME]) > 0:
                    product_in_order = ProductInOrder(
                        product=customer_product,
                        amount=int(row[self._QUANTITY_COLUMN_NAME]),
                        order=order,
                    )
                    product_in_order.save()
        self.customer_order.products.add(*unique_customer_products)

        return []

    def _parse_products(self, df: pd.DataFrame) -> None:
        pass

    def _create_orders(self, df: pd.DataFrame, tp_list: list[TradePoint]) -> None:
        pass

    def parse(self) -> None:
        dfs = self._read()
        _ = self._parse_trade_points(dfs)
        # tp_list = self._parse_trade_points(dfs)
        # self._parse_products(df)
        # self._create_orders(df, tp_list)


class ProdstarrParser(Parser):
    _PRODUCT_COLUMN_NAME = "Контрагент"
    _SKIPROWS = 5

    def _read(self) -> pd.DataFrame:
        try:
            df = pd.read_excel(
                self.file,
                skiprows=self._SKIPROWS,
                engine="openpyxl",
            )
            # df = df.drop(df.columns[0], axis=1)  # удаляем первую колонку с Артикулом
            df = df.drop(0)
            df = df.drop(df.columns[[1, 2, 3, 4]], axis=1)
        except Exception as e:
            print("Не получилось обработать файл", e)
            raise

        # Заполняем пустые ячейки нулями
        df = df.fillna(0)

        # logger.debug("df: {}", df)

        if df.empty:
            print("Из файла не загрузилось ни одной строки!")

        return df

    def _parse_trade_points(self, df: pd.DataFrame) -> list[TradePoint]:
        tp_list = []
        tp_names = df.columns.tolist()

        tp_names.remove(self._PRODUCT_COLUMN_NAME)
        tp_names = [tp_name for tp_name in tp_names if "Unnamed" not in tp_name]
        for tp_name in tp_names:
            tp, _ = TradePoint.objects.get_or_create(name=tp_name, customer=self.customer)
            if any([qty for qty in df[tp_name].tolist()]):
                tp_list.append(tp)
        return tp_list

    def _parse_products(self, df: pd.DataFrame) -> None:
        products_from_file = df[self._PRODUCT_COLUMN_NAME].tolist()
        # logger.debug("products_from_file: {}", products_from_file)

        # Create products if not exist
        for row_num in range(len(products_from_file)):
            customer_product, _ = CustomerProduct.objects.get_or_create(
                name=products_from_file[row_num],
                customer=self.customer,
            )

    def _create_orders(self, df: pd.DataFrame, tp_list: list[TradePoint]) -> None:
        unique_customer_products = []
        for tp in tp_list:
            products_in_order: list[ProductInOrder] = []

            for _, row in df.iterrows():
                # logger.debug("row: {}", row[tp.name])
                if row[tp.name] > 0:
                    customer_product = CustomerProduct.objects.get(
                        name=row[self._PRODUCT_COLUMN_NAME],
                    )
                    product_in_order = ProductInOrder(
                        product=customer_product,
                        amount=int(row[tp.name]),
                    )
                    products_in_order.append(product_in_order)

                    if customer_product not in unique_customer_products:
                        unique_customer_products.append(customer_product)

            if products_in_order:
                order = Order(
                    customer_order=self.customer_order,
                    trade_point=tp,
                )
                order.save()
                for product_in_order in products_in_order:
                    product_in_order.order = order
                    product_in_order.save()
        self.customer_order.products.add(*unique_customer_products)

    def parse(self):
        df = self._read()

        tp_list = self._parse_trade_points(df)
        self._parse_products(df)
        self._create_orders(df, tp_list)


class ParserFactory:
    def create_parser(self, customer_order_code: str) -> type[Parser]:
        if customer_order_code == "stroytorgovlya":
            return StroiTorgovlyaParser
        elif customer_order_code == "oseni":
            return OseniParserV2
        elif customer_order_code == "kruasan":
            return KruasanParser
        elif customer_order_code == "prodstarr":
            return ProdstarrParser
        elif customer_order_code == "lavki-bakhusa":
            return BahusParser
        else:
            raise ValueError("Customer parser does not exist.")
