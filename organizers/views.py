from django.shortcuts import render
from .models import Event
from .serializers import EventCreateSerializer,EventListSerializer
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .permissions import IsEventOrganizer,IsOrganizer
from accounts.serializers import UserSerializer
from attendee.models import Ticket
from django.shortcuts import get_object_or_404
from attendee.serializers import AttendeeSerializer




class CreateEvent(generics.CreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventCreateSerializer
    permission_classes = [IsAuthenticated,IsOrganizer]

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

class UpdateEvent(generics.UpdateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventCreateSerializer
    permission_classes = [IsAuthenticated,IsEventOrganizer]
    lookup_field = 'pk'
    

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

class DeleteEvent(generics.DestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventCreateSerializer
    permission_classes = [IsAuthenticated, IsEventOrganizer]
    lookup_field = "pk"


class OrganizerEvents(generics.ListAPIView):
    serializer_class = EventListSerializer
    permission_classes = [IsAuthenticated,IsOrganizer]

    def get_queryset(self):
        organizer = self.request.user
        return Event.objects.filter(organizer=organizer)

class EventAttendees(generics.ListAPIView):
    serializer_class = AttendeeSerializer
    permission_classes = [IsAuthenticated, IsOrganizer, IsEventOrganizer]

    def get_queryset(self):
        event_id = self.kwargs.get("id")

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
        
