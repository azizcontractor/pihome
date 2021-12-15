from django.urls import path

from . import views

app_name = "home"

urlpatterns = [
    path("", views.index, name="index"),
    path("system/stats", views.get_stats, name="stats"),
]
