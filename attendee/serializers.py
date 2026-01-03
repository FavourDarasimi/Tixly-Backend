from rest_framework import serializers
from .models import Ticket
from organizers.serializers import EventListSerializer,TicketTierSerializer

class AttendeeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    name = serializers.CharField(source="attendee_name", read_only=True)
    ticket_tier = serializers.CharField(source="ticket_tier.name", read_only=True)

    class Meta:
        model = Ticket
        fields = (
            "id",
            "name",
            "email",
            "ticket_tier",
            "status",
            "created_at",
        )    

class TicketSerializer(serializers.ModelSerializer):
    event = EventListSerializer(read_only=True)
    ticket_tier = TicketTierSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields =["event","user","ticket_tier","qr_code","status","created_at"]       