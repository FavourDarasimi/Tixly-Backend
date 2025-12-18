from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from organizers.serializers import EventListSerializer,TicketTierSerializer
from rest_framework import generics, filters
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Event,TicketTier
from .filters import EventFilter



class ListEvents(generics.ListAPIView):
    queryset = Event.objects.filter(status='published').select_related(
        'organizer'
    ).prefetch_related(
        'ticket_tiers'
    ).order_by('startDateTime')
    
    serializer_class = EventListSerializer
    permission_classes = [AllowAny]
    
    # Enable filtering backends
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    
    # Configure DjangoFilterBackend
    filterset_class = EventFilter
    
    # Configure SearchFilter
    search_fields = [
        'title',
        'description',
        'location',
    
        'category'
    ]
    
    # Configure OrderingFilter
    ordering_fields = [
        'title',
        'data',
        'startDateTime',
        'endDateTime',
        'createdAt',
    ]
    ordering = ['startDateTime']  # Default ordering
    
    def get_queryset(self):
        """
        Optionally restricts the returned events,
        by filtering against query parameters in the URL.
        """
        queryset = super().get_queryset()
        
        # Additional custom filtering logic can go here
        # For example, only show future events
        from django.utils import timezone
        queryset = queryset.filter(startDateTime__gte=timezone.now())
        
        return queryset
    

class EventDetails(generics.RetrieveAPIView):
    queryset = Event.objects.all()
    serializer_class = EventListSerializer
    lookup_field = 'pk'    

class EventTicketTiers(generics.ListAPIView):
    serializer_class = TicketTierSerializer
   

    def get_queryset(self):
        event_id = self.kwargs.get("pk")
        return TicketTier.objects.filter(event__id = event_id)

# Create your views here.
