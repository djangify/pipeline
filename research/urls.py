# research/urls.py -- frontend pages. API routes live in research/api_urls.py.
from django.urls import path

from . import views

app_name = "research"

urlpatterns = [
    path("", views.ResearchHomeView.as_view(), name="home"),
    path("<str:business>/", views.ResearchBusinessView.as_view(), name="business_detail"),
]
