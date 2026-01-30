from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from organizers.serializers import EventListSerializer,TicketTierSerializer,EventDetailSerializer
from rest_framework import generics, filters
from rest_framework.permissions import AllowAny,IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import TicketSerializer
from .models import Event,TicketTier,Ticket,Order, SavedEvent
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
    Get events happening in the next 24 hours, week, month etc.
    Optimized to use DB-level filtering.
    """
    serializer_class = EventListSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        now = timezone.now()
        user = request.user
        
        # Base QuerySet: All future events the user has a ticket for
        # distinct() is crucial because a user might have multiple tickets for one event
        # Note: related_name='event' on Ticket model means we use event__user to filter
        base_qs = Event.objects.filter(
            event__user=user, 
            startDateTime__gte=now
        ).distinct().select_related(
            'organizer'
        ).prefetch_related(
            'ticket_tiers'
        )

        # Derived QuerySets
        twenty_four_hrs = now + timedelta(hours=24)
        week = now + timedelta(days=7)
        month = now + timedelta(days=30)

        events_24h = base_qs.filter(startDateTime__lte=twenty_four_hrs).order_by('startDateTime')
        events_week = base_qs.filter(startDateTime__lte=week).order_by('startDateTime')
        events_month = base_qs.filter(startDateTime__lte=month).order_by('startDateTime')
        events_all = base_qs.order_by('startDateTime')

        serializer = self.get_serializer
        return Response({
            "next_24_hours": serializer(events_24h, many=True).data,
            "this week": serializer(events_week, many=True).data, # Kept original key 'this week' for compatibility
            "this_month": serializer(events_month, many=True).data,
            "all": serializer(events_all, many=True).data
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

class AttendeeEvents(generics.GenericAPIView):
    serializer_class = EventListSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        user = request.user
        
        # Base QuerySet: All events user has tickets for
        # Note: related_name='event' on Ticket model means we use event__user to filter
        base_qs = Event.objects.filter(
            event__user=user
        ).distinct().select_related(
            'organizer'
        ).prefetch_related(
            'ticket_tiers'
        )
        
        # Split into upcoming and past
        upcoming_events = base_qs.filter(startDateTime__gt=now).order_by('startDateTime')
        past_events = base_qs.filter(startDateTime__lte=now).order_by('-startDateTime')
        
        serializer = self.get_serializer

        return Response({
            "upcoming": serializer(upcoming_events, many=True).data,
            "past": serializer(past_events, many=True).data
        })


class EventTicket(generics.ListAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        pk = self.kwargs.get("pk")
        user = self.request.user
        ticket = Ticket.objects.filter(event__id = pk,user =user ).select_related('event','event__organizer','ticket_tier').prefetch_related('event__ticket_tiers')
        return ticket




# ============ SAVED EVENTS ============

class SavedEventsList(generics.GenericAPIView):
    """
    List saved events or toggle save status for an event
    """
    serializer_class = EventListSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List all events saved by the user"""
        user = request.user
        
        # Get events that are in the user's saved_events list
        saved_events = Event.objects.filter(
            saved_by__user=user
        ).select_related(
            'organizer'
        ).prefetch_related(
            'ticket_tiers'
        ).order_by('-saved_by__created_at')
        
        serializer = self.get_serializer(saved_events, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Toggle save status for an event"""
        event_id = request.data.get('event_id')
        if not event_id:
            return Response(
                {"error": "event_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        from .models import SavedEvent
        
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response(
                {"error": "Event not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Check if already saved
        saved_event = SavedEvent.objects.filter(user=request.user, event=event).first()
        
        if saved_event:
            # Unsave
            saved_event.delete()
            return Response(
                {"status": "unsaved", "message": "Event removed from saved list"}
            )
        else:
            # Save
            SavedEvent.objects.create(user=request.user, event=event)
            return Response(
                {"status": "saved", "message": "Event saved successfully"}
            )

class RecommendedEvents(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EventListSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        now = timezone.now()

        # 1. Gather User Interests (Categories)
        purchased_categories = Order.objects.filter(user=user).values_list('event__category', flat=True)
        saved_categories = SavedEvent.objects.filter(user=user).values_list('event__category', flat=True)
        
        # Combine and deduplicate categories
        interested_categories = set(purchased_categories) | set(saved_categories)

        # 2. Base Query for Events (Published & Upcoming)
        queryset = Event.objects.filter(
            status='published',
            startDateTime__gte=now
        )

        # 3. Exclude events the user has already bought tickets for OR saved
        purchased_event_ids = Order.objects.filter(user=user).values_list('event_id', flat=True)
        saved_event_ids = SavedEvent.objects.filter(user=user).values_list('event_id', flat=True)
        
        queryset = queryset.exclude(id__in=purchased_event_ids).exclude(id__in=saved_event_ids)

        # 4. Filter by Interest (if any)
        if interested_categories:
            # Events in interested categories
            recommended_queryset = queryset.filter(category__in=interested_categories)
            
            # If we have results, return them. 
            # We can also mix in some "popular" events if the list is short, but let's keep it simple for now.
            if recommended_queryset.exists():
                return recommended_queryset.order_by('startDateTime')[:10]
        
        # 5. Fallback (Cold Start or No Matches)
        # Return upcoming events, perhaps sorted by popularity (if we had a sales count) or just date
        # For now, just upcoming events
        return queryset.order_by('startDateTime')[:10]
