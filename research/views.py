# research/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.http import Http404
from django.views.generic import TemplateView
from rest_framework import viewsets

from .models import CompetitorAd, Keyword, PainTheme
from .serializers import CompetitorAdSerializer, KeywordSerializer, PainThemeSerializer


# ---------------------------------------------------------------------------
# Frontend views
# ---------------------------------------------------------------------------
def _known_businesses():
    """Every business name used in any research table, sorted. There is no fixed
    list: a business appears here as soon as a pain theme, ad or keyword is
    saved against it."""
    names = set()
    for model in (PainTheme, CompetitorAd, Keyword):
        names.update(model.objects.order_by().values_list("business", flat=True).distinct())
    return sorted((n for n in names if n), key=str.lower)


class ResearchHomeView(LoginRequiredMixin, TemplateView):
    template_name = "research/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["businesses"] = [
            {
                "key": name,
                "label": name,
                "pain_theme_count": PainTheme.objects.filter(business=name).count(),
                "ad_count": CompetitorAd.objects.filter(business=name).count(),
                "keyword_count": Keyword.objects.filter(business=name).count(),
            }
            for name in _known_businesses()
        ]
        return context


class ResearchBusinessView(LoginRequiredMixin, TemplateView):
    template_name = "research/business_detail.html"

    def get_context_data(self, **kwargs):
        business = self.kwargs["business"]
        if business not in _known_businesses():
            raise Http404("Unknown business")

        context = super().get_context_data(**kwargs)
        context["business"] = business
        context["business_label"] = business
        context["pain_themes"] = PainTheme.objects.filter(business=business).order_by("-quote_count")
        context["keywords"] = Keyword.objects.filter(business=business).order_by(
            F("search_volume").desc(nulls_last=True)
        )

        ads_by_competitor = {}
        for ad in CompetitorAd.objects.filter(business=business).order_by("competitor_name", "-date_pulled"):
            ads_by_competitor.setdefault(ad.competitor_name, []).append(ad)
        context["ads_by_competitor"] = ads_by_competitor
        return context


# ---------------------------------------------------------------------------
# API views
# ---------------------------------------------------------------------------


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
