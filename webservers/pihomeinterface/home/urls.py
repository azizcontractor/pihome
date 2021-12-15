from django.urls import path

from . import views

app_name = "home"

urlpatterns = [
    path("", views.index, name="index"),
    path("show/info", views.show_info, name="show_info"),
    path("show/slides", views.show_slides, name="show_slides"),
    path("show/system", views.show_system, name="show_system"),
    path("toggle/notifications", views.toggle_notifications, name="toggle_notify"),
    path("clear/notifications", views.clear_notifications, name="clear_notify"),
    path("system/reboot", views.system_reboot, name="reboot"),
]
