from django.urls import include, path

app_name = "api"
urlpatterns = [
    path("users/", include("backend.users.urls", namespace="users")),
    path("", include("backend.orders.urls", namespace="orders")),
]
