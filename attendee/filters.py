from django_filters import rest_framework as django_filters
from .models import Event
from django.db.models import Q


class EventFilter(django_filters.FilterSet):
    """Custom filter class for Event filtering"""
    
    category = django_filters.CharFilter(field_name='category', lookup_expr='iexact')
    location = django_filters.CharFilter(method='filter_location')
    date = django_filters.DateFilter(method='filter_date')
    start_date = django_filters.DateFilter(field_name='startDateTime', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='endDateTime', lookup_expr='lte')
    min_price = django_filters.NumberFilter(method='filter_min_price')
    max_price = django_filters.NumberFilter(method='filter_max_price')
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    
    class Meta:
        model = Event
        fields = ['category', 'location', 'date', 'status']
    
    def filter_location(self, queryset, name, value):
        """Filter by location - searches in both location and address fields"""
        return queryset.filter(
            Q(location__icontains=value) | Q(address__icontains=value)
        )
    
    def filter_date(self, queryset, name, value):
        """Filter events happening on a specific date"""
        return queryset.filter(
            startDateTime__date=value
        )
    
    def filter_min_price(self, queryset, name, value):
        """Filter events with tickets >= min_price"""
        return queryset.filter(
            ticket_tiers__price__gte=value
        ).distinct()
    
    def filter_max_price(self, queryset, name, value):
        """Filter events with tickets <= max_price"""
        return queryset.filter(
            ticket_tiers__price__lte=value
        ).distinct()
