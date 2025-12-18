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

