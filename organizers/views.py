from django.shortcuts import render
from .models import Event,TicketTier
from .serializers import EventCreateSerializer,EventListSerializer,TicketTierSerializer
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework.permissions import  IsAdminUser
from .permissions import IsEventOrganizer,IsOrganizer
from accounts.serializers import UserSerializer
from attendee.models import Ticket
from django.shortcuts import get_object_or_404
from attendee.serializers import AttendeeSerializer
from .models import Event, TicketTier, Speaker, Schedule, EventDay
from .serializers import (
    EventCreateSerializer, EventListSerializer, EventDetailSerializer,
    TicketTierSerializer, SpeakerSerializer, ScheduleSerializer,
    ScheduleListSerializer, EventDayWithScheduleSerializer
)
from django.db.models import Prefetch


class CreateEvent(generics.CreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventCreateSerializer
    permission_classes = [IsOrganizer]

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

class UpdateEvent(generics.UpdateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventCreateSerializer
    permission_classes = [IsEventOrganizer]
    lookup_field = 'pk'
    

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

class DeleteEvent(generics.DestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventCreateSerializer
    permission_classes = [IsEventOrganizer]
    lookup_field = "pk"


class OrganizerEvents(generics.ListAPIView):
    serializer_class = EventListSerializer
    permission_classes = [IsOrganizer]

    def get_queryset(self):
        organizer = self.request.user
        return Event.objects.filter(organizer=organizer)

class EventAttendees(generics.ListAPIView):
    serializer_class = AttendeeSerializer
    permission_classes = [IsOrganizer, IsEventOrganizer]

    def get_queryset(self):
        event_id = self.kwargs.get("pk")

        event = get_object_or_404(Event, id=event_id)

        # Object-level permission check
        self.check_object_permissions(self.request, event)

        return (
            Ticket.objects
            .filter(
                order__event=event,
                order__status="paid",
            )
            .select_related("user", "ticket_tier", "order")
            .order_by("-created_at")
        )
        
class CreateTicketTiers(generics.CreateAPIView):
    serializer_class = TicketTierSerializer
    permission_classes = [IsOrganizer]

    def perform_create(self, serializer):
        event_id = self.kwargs.get("pk")
        event = Event.objects.get(id=event_id)
        serializer.save(event=event)
        return super().perform_create(serializer)
    
class UpdateTicketTier(generics.UpdateAPIView):    
    queryset = TicketTier.objects.all()
    serializer_class = TicketTierSerializer
    permission_classes = [IsEventOrganizer]
    lookup_field = 'pk'

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)
    
class DeleteTicketTier(generics.DestroyAPIView):
    queryset = TicketTier.objects.all()
    serializer_class = TicketTierSerializer
    permission_classes = [IsEventOrganizer]
    lookup_field = "pk"










# Add these views to organizers/views.py




# ============ SPEAKER VIEWS ============

class CreateSpeaker(generics.CreateAPIView):
    """Create a new speaker"""
    serializer_class = SpeakerSerializer
    permission_classes = [IsOrganizer]
    
    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)


class ListSpeakers(generics.ListAPIView):
    """List all speakers created by the organizer"""
    serializer_class = SpeakerSerializer
    permission_classes = [IsOrganizer]
    
    def get_queryset(self):
        return Speaker.objects.filter(
            organizer=self.request.user
        ).order_by('-created_at')


class SpeakerDetail(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a speaker"""
    serializer_class = SpeakerSerializer
    permission_classes = [IsOrganizer]
    lookup_field = 'pk'
    
    def get_queryset(self):
        # Only allow organizers to access their own speakers
        return Speaker.objects.filter(organizer=self.request.user)
    
    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


# ============ SCHEDULE VIEWS ============

class CreateSchedule(generics.CreateAPIView):
    """Create a schedule item for an event"""
    serializer_class = ScheduleSerializer
    permission_classes = [IsEventOrganizer]
    
    def perform_create(self, serializer):
        event_id = self.kwargs.get('event_id')
        event = get_object_or_404(Event, id=event_id)
        
        # # Check if user is the event organizer
        # if event.organizer != self.request.user:
        #     from rest_framework.exceptions import PermissionDenied
        #     raise PermissionDenied("You don't have permission to add schedule to this event")
        
        serializer.save(event=event)


class ListEventSchedules(generics.ListAPIView):
    """List all schedules for an event"""
    serializer_class = ScheduleListSerializer

    
    def get_queryset(self):
        event_id = self.kwargs.get('event_id')
        return Schedule.objects.filter(
            event_id=event_id
        ).select_related(
            'event', 'event_day'
        ).prefetch_related(
            'speakers'
        ).order_by('date', 'start_time', 'order')


class ScheduleDetail(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a schedule item"""
    serializer_class = ScheduleSerializer
    permission_classes = [IsOrganizer]
    lookup_field = 'pk'
    
    def get_queryset(self):
        # Only allow organizers to access schedules for their events
        return Schedule.objects.filter(
            event__organizer=self.request.user
        ).select_related('event').prefetch_related('speakers')
    
    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


class BulkCreateSchedules(generics.GenericAPIView):
    """Bulk create multiple schedule items at once"""
    serializer_class = ScheduleSerializer
    permission_classes = [IsEventOrganizer]
    
    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        
        # Check permission
        # if event.organizer != self.request.user:
        #     from rest_framework.exceptions import PermissionDenied
        #     raise PermissionDenied("You don't have permission to add schedule to this event")
        
        schedules_data = request.data.get('schedules', [])
        
        if not isinstance(schedules_data, list):
            return Response(
                {'error': 'schedules must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_schedules = []
        errors = []
        
        for idx, schedule_data in enumerate(schedules_data):
            serializer = self.get_serializer(data=schedule_data)
            if serializer.is_valid():
                schedule = serializer.save(event=event)
                created_schedules.append(serializer.data)
            else:
                errors.append({
                    'index': idx,
                    'errors': serializer.errors
                })
        
        response_data = {
            'created': len(created_schedules),
            'schedules': created_schedules
        }
        
        if errors:
            response_data['errors'] = errors
        
        return Response(
            response_data,
            status=status.HTTP_201_CREATED if created_schedules else status.HTTP_400_BAD_REQUEST
        )


class EventSchedulesByDate(generics.GenericAPIView):
    """Get event schedules grouped by date"""
    serializer_class = ScheduleListSerializer

    
    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        
        schedules = Schedule.objects.filter(
            event=event
        ).select_related(
            'event', 'event_day'
        ).prefetch_related(
            'speakers'
        ).order_by('date', 'start_time', 'order')
        
        # Group by date
        schedules_by_date = {}
        for schedule in schedules:
            date_str = schedule.date.isoformat()
            if date_str not in schedules_by_date:
                schedules_by_date[date_str] = []
            schedules_by_date[date_str].append(
                self.get_serializer(schedule).data
            )
        
        return Response({
            'event_id': event.id,
            'event_title': event.title,
            'start_date': event.startDateTime.date().isoformat() if event.startDateTime else None,
            'end_date': event.endDateTime.date().isoformat() if event.endDateTime else None,
            'is_multi_day': event.is_multi_day,
            'schedules_by_date': schedules_by_date
        })


class EventDaySchedules(generics.ListAPIView):
    """Get schedules for a specific event day"""
    serializer_class = ScheduleListSerializer
    
    def get_queryset(self):
        event_day_id = self.kwargs.get('event_day_id')
        return Schedule.objects.filter(
            event_day_id=event_day_id
        ).select_related(
            'event', 'event_day'
        ).prefetch_related(
            'speakers'
        ).order_by('start_time', 'order')


# ============ EVENT DAY VIEWS (for multi-day events) ============

class CreateEventDay(generics.CreateAPIView):
    """Create an event day for multi-day events"""
    serializer_class = EventDayWithScheduleSerializer
    permission_classes = [IsOrganizer]
    
    def perform_create(self, serializer):
        event_id = self.kwargs.get('event_id')
        event = get_object_or_404(Event, id=event_id)
        
        if event.organizer != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to modify this event")
        
        serializer.save(event=event)


class ListEventDays(generics.ListAPIView):
    """List all event days with their schedules"""
    serializer_class = EventDayWithScheduleSerializer
    permission_classes = []  # Public view
    
    def get_queryset(self):
        event_id = self.kwargs.get('event_id')
        return EventDay.objects.filter(
            event_id=event_id
        ).prefetch_related(
            Prefetch(
                'schedules',
                queryset=Schedule.objects.prefetch_related('speakers').order_by('start_time', 'order')
            )
        ).order_by('date', 'startTime')


class EventDayDetail(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an event day"""
    serializer_class = EventDayWithScheduleSerializer
    permission_classes = [IsOrganizer]
    lookup_field = 'pk'
    
    def get_queryset(self):
        return EventDay.objects.filter(
            event__organizer=self.request.user
        ).select_related('event')
    
    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)