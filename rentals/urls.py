from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("terms/", views.terms, name="terms"),
    path("products/", views.product_list, name="product_list"),
    path("products/new/", views.register_product, name="register_product"),
    path("products/<int:pk>/", views.product_detail, name="product_detail"),
    path("products/<int:pk>/book/", views.create_booking, name="create_booking"),
    path("register/", views.register, name="register"),
    path("orders/", views.orders, name="orders"),
    path("orders/<int:pk>/condition/", views.condition_report, name="condition_report"),
    path("orders/<int:pk>/chat/", views.chat_room, name="chat_room"),
    path("orders/<int:pk>/messages/", views.messages_api, name="messages_api"),
    path("orders/<int:pk>/complaint/", views.report_complaint, name="report_complaint"),
    path("orders/<int:pk>/<str:action>/", views.booking_action, name="booking_action"),
    path("contact/", views.contact, name="contact"),
    path("feedback/", views.feedback, name="feedback"),
]
