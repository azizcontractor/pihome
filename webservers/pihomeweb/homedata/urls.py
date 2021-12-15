from django.urls import path

from . import views

app_name = "homedata"

urlpatterns = [
    path("", views.index, name="index"),
    path("solar/", views.load_solar_data, name="solar"),
    path("sensor/", views.load_sensor_data, name="sensor"),
    path("network/", views.load_network_data, name="sensor"),
]
