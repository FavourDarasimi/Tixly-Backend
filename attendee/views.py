from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from organizers.serializers import EventListSerializer,TicketTierSerializer
from rest_framework import generics, filters
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Event,TicketTier
from .filters import EventFilter
from django.utils import timezone
from datetime import timedelta



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
    

class UpcomingEvents(generics.ListAPIView):
    """
    Get events happening in the next 24 hours
    """
    serializer_class = EventListSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        now = timezone.now()
        twenty_four_hours_later = now + timedelta(hours=24)
        
        return Event.objects.filter(
            status='published',
            startDateTime__gte=now,
            startDateTime__lte=twenty_four_hours_later
        ).select_related(
            'organizer'
        ).prefetch_related(
            'ticket_tiers',
            'saved_by'
        ).order_by('startDateTime')


class NewEvents(generics.ListAPIView):
    """
    Get newly created events (created in the last 7 days)
    """
    serializer_class = EventListSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        return Event.objects.filter(
            status='published',
            created_at__gte=seven_days_ago,
            startDateTime__gte=timezone.now()
        ).select_related(
            'organizer'
        ).prefetch_related(
            'ticket_tiers',
            'saved_by'
        ).order_by('-created_at')

class EventDetails(generics.RetrieveAPIView):
  
    queryset = Event.objects.all()
    serializer_class = EventListSerializer
    permission_classes = [AllowAny]
    lookup_field = 'pk'
    
    def retrieve(self, request, *args, **kwargs):
        """Override to increment view count"""
        instance = self.get_object()
        
        # Increment views (but not for the organizer viewing their own event)
        if not request.user.is_authenticated or request.user != instance.organizer:
            instance.increment_views()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)    

class EventTicketTiers(generics.ListAPIView):
    serializer_class = TicketTierSerializer
   

    def get_queryset(self):
        event_id = self.kwargs.get("pk")
        return TicketTier.objects.filter(event__id = event_id)

# Create your views here.
