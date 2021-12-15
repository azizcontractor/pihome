from django.urls import path

from . import views

app_name = "pidata"

urlpatterns = [
    path("time/", views.load_time, name="time"),
    path("location/", views.load_location, name="location"),
    path("weather/", views.load_weather, name="weather"),
    path("quote/", views.load_quote, name="quote"),
    path("notifications/", views.load_notifications, name="notifications"),
    path("clear_notification/", views.clear_notification, name="clear_notif"),
    path("clear_all_notifications/", views.clear_all_notifications, name="clear_all_notif"),
]
