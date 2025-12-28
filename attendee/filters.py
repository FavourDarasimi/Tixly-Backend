from django_filters import rest_framework as django_filters
from .models import Event
from django.db.models import Q
from django.utils import timezone


class EventFilter(django_filters.FilterSet):
    
    category = django_filters.CharFilter(field_name='category', lookup_expr='iexact')
    location = django_filters.CharFilter(method='filter_location')
    date = django_filters.DateFilter(method='filter_date')
    start_date = django_filters.DateFilter(field_name='startDateTime', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='endDateTime', lookup_expr='lte')
    min_price = django_filters.NumberFilter(method='filter_min_price')
    max_price = django_filters.NumberFilter(method='filter_max_price')
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    date_range = django_filters.DateFromToRangeFilter(method='filter_date_range')
    is_multi_day = django_filters.BooleanFilter(field_name='isMultiDay')
    currently_happening = django_filters.BooleanFilter(method='filter_currently_happening')
    
    class Meta:
        model = Event
        fields = ['category', 'location', 'date', 'status','is_multi_day']
    
    def filter_location(self, queryset, name, value):
        return queryset.filter(
            Q(location__icontains=value) | Q(address__icontains=value)
        )
    
    def filter_date(self, queryset, name, value):
        return queryset.filter(
            startDateTime__date=value
        )
    
    def filter_min_price(self, queryset, name, value):
        return queryset.filter(
            ticket_tiers__price__gte=value
        ).distinct()
    
    def filter_max_price(self, queryset, name, value):
        return queryset.filter(
            ticket_tiers__price__lte=value
        ).distinct()
    
    def filter_happening_on_date(self, queryset, name, value):
        return queryset.filter(
            startDateTime__date__lte=value,
            endDateTime__date__gte=value
        )
    
    def filter_starts_after(self, queryset, name, value):
        return queryset.filter(startDateTime__date__gte=value)
    
    def filter_ends_before(self, queryset, name, value):
        return queryset.filter(endDateTime__date__lte=value)
    
    def filter_date_range(self, queryset, name, value):
        if value.start and value.stop:
            return queryset.filter(
                Q(startDateTime__date__lte=value.stop) &
                Q(endDateTime__date__gte=value.start)
            )
        return queryset
    
    def filter_currently_happening(self, queryset, name, value):
        if value:
            now = timezone.now()
            return queryset.filter(
                startDateTime__lte=now,
                endDateTime__gte=now,
                status='published'
            )
        return queryset
