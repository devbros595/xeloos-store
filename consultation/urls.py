from django.urls import path
from . import views

urlpatterns = [
    path("", views.book_consultation, name="consultation"),
    path("message-sent-successfully/", views.consultation_success, name="consultation_success"),
]