# research/urls.py
from rest_framework.routers import DefaultRouter

from . import views

app_name = "research"

router = DefaultRouter()
router.register(r"ads", views.CompetitorAdViewSet)
router.register(r"keywords", views.KeywordViewSet)
router.register(r"pain-themes", views.PainThemeViewSet)

urlpatterns = router.urls
