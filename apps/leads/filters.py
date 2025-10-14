"""
Фильтры для приложения leads.
"""

from django_filters import FilterSet

from .models import PotentialClient


class LeadFilter(FilterSet):
    class Meta:
        model = PotentialClient
        # Фильтр по рекламной кампании (выпадающий список)
        fields = ["ad_campaign"]
