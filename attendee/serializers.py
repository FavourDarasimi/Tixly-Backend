from rest_framework import serializers
from .models import Ticket

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