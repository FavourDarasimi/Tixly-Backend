from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from organizers.serializers import EventListSerializer,TicketTierSerializer,EventDetailSerializer
from rest_framework import generics, filters
from rest_framework.permissions import AllowAny,IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Event,TicketTier,Ticket
from .filters import EventFilter
from django.utils import timezone
from datetime import timedelta
from django.db.models import Prefetch
from organizers.models import Schedule,EventDay
from django.db.models import Count, Exists, OuterRef




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
        queryset = queryset.filter(endDateTime__gte=timezone.now())
        
        return queryset
    

# class TrendingEvents(generics):
#     pass

class UpcomingEvents(generics.GenericAPIView):
    """
    Get events happening in the next 24 hours
    """
    serializer_class = EventListSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self,request):
        now = timezone.now()
        user = request.user
        twenty_four_hrs = now + timedelta(hours=24)
        week = now + timedelta(days=7)
        month = now + timedelta(days=30)
        tickets = Ticket.objects.filter(user=user,event__startDateTime__gte=now).select_related('event','event__organizer','ticket_tier').prefetch_related('event__ticket_tiers').order_by('event__startDateTime')
        events_24h = []
        events_week = []
        events_month = []
        events_all = []
     
        seen_event_ids = set()
        for ticket in tickets:
            event =ticket.event
            if event.id in seen_event_ids:
                continue
            seen_event_ids.add(event.id)
            if event.startDateTime <= twenty_four_hrs:
                events_24h.append(event)
            if event.startDateTime <= week:       
                events_week.append(event)
            if event.startDateTime <= month:       
                events_month.append(event)
            events_all.append(event)    

        serializer = self.serializer_class   
        return Response({
            "next_24_hours":serializer(events_24h,many=True).data,
            "this week":serializer(events_week,many=True).data,
            "this_month":serializer(events_month,many=True).data,
            "all":serializer(events_all,many=True).data
        })      

  


class NewEvents(generics.ListAPIView):
    """
    Get newly created events (created in the last 7 days)
    """
    serializer_class = EventListSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        seven_days_ago = timezone.now() - timedelta(days=20)
        
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
  
 
    serializer_class = EventDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'pk'


    def get_queryset(self):
        return Event.objects.select_related(
            'organizer'
        ).prefetch_related(
            'ticket_tiers',
            Prefetch(
                'schedules',
                queryset=Schedule.objects.select_related(
                    'event_day'
                ).prefetch_related(
                    'speakers'
                ).order_by('date', 'start_time', 'order')
            ),
            Prefetch(
                'event_days',
                queryset=EventDay.objects.prefetch_related(
                    Prefetch(
                        'schedules',
                        queryset=Schedule.objects.prefetch_related('speakers')
                    )
                ).order_by('date', 'startTime')
            )
        )

    
    # def retrieve(self, request, *args, **kwargs):
    #     """Override to increment view count"""
    #     instance = self.get_object()
        
    #     # Increment views (but not for the organizer viewing their own event)
    #     if not request.user.is_authenticated or request.user != instance.organizer:
    #         instance.increment_views()
        
    #     serializer = self.get_serializer(instance)
    #     return Response(serializer.data)    

class EventTicketTiers(generics.ListAPIView):
    serializer_class = TicketTierSerializer
   

    def get_queryset(self):
        event_id = self.kwargs.get("pk")
        return TicketTier.objects.filter(event__id = event_id)

# Create your views here.
