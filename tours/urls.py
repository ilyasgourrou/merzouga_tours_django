from django.urls import path
from . import views

app_name = "tours"

urlpatterns = [
    path("", views.home, name="home"),
    path("circuits/", views.tour_list, name="tour_list"),
    path("circuits/<slug:slug>/", views.tour_detail, name="tour_detail"),
    path("a-propos/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("reservation/<str:reference>/", views.reservation_detail, name="reservation_detail"),
    path("reservation/<str:reference>/whatsapp/", views.reservation_whatsapp, name="reservation_whatsapp"),
]
