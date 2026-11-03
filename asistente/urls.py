from django.urls import path

from . import views

app_name = "asistente"

urlpatterns = [
    path("catalogo.json", views.catalogo_json, name="catalogo_json"),
]
