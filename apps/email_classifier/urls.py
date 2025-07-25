from django.urls import path
from .views import EmailInquiryView

urlpatterns = [
    path("inquiry/", EmailInquiryView.as_view(), name="inquiry"),
]