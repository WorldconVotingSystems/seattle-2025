from django.urls import path

from . import views

app_name = "seattle_2025_app"

urlpatterns = [
    path("controll-redirect/", views.controll_redirect, name="controll-redirect"),
]
