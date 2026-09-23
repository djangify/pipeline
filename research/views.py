# research/views.py
from rest_framework import viewsets

from .models import CompetitorAd, Keyword, PainTheme
from .serializers import CompetitorAdSerializer, KeywordSerializer, PainThemeSerializer


class BusinessFilteredViewSet(viewsets.ModelViewSet):
    """Optional ?business=<key> filter, shared by all three research viewsets."""

    def get_queryset(self):
        qs = self.queryset
        business = self.request.query_params.get("business")
        if business:
            qs = qs.filter(business=business)
        return qs


class CompetitorAdViewSet(BusinessFilteredViewSet):
    queryset = CompetitorAd.objects.all()
    serializer_class = CompetitorAdSerializer


class KeywordViewSet(BusinessFilteredViewSet):
    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer


class PainThemeViewSet(BusinessFilteredViewSet):
    queryset = PainTheme.objects.all()
    serializer_class = PainThemeSerializer
