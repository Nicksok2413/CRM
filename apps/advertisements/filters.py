"""
Фильтры для приложения advertisements.
"""

from django_filters import FilterSet

from .models import AdCampaign


class AdCampaignFilter(FilterSet):
    class Meta:
        model = AdCampaign
        # Фильтр по каналу (выпадающий список) и услуге (выпадающий список)
        fields = ["channel", "service"]
