from django.urls import path

from . import views

app_name = "piframe"

urlpatterns = [
    path("", views.index, name="index"),
    path("load_image/", views.load_image, name="load_img"),
    path("manage/", views.manage_images, name="manage"),
    path("delete_image/", views.delete_image, name="delete"),
    # path("toggle_lights/", views.toggle_lights, name="toggle"),
]
