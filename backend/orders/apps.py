from django.apps import AppConfig


class OrdersConfig(AppConfig):
    name = "backend.orders"

    def ready(self):
        try:
            import backend.orders.signals  # noqa: F401
        except ImportError:
            pass
