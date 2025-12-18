from rest_framework import serializers
from .models import Event,TicketTier,Coupon
from accounts.models import User
from attendee.models import Ticket


class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class TicketTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketTier
        fields = '__all__'
        # event is optional here if you create tickets via a nested route
        # e.g., POST /events/5/tickets/
        extra_kwargs = {'event': {'read_only': True}}


class EventListSerializer(serializers.ModelSerializer):
    organizer = UserPublicSerializer(read_only=True)
    
    # Reverse relationship: Show all tickets associated with this event
    # Note: 'ticket_types' matches the related_name in your TicketTier model
    ticket_tiers = TicketTierSerializer(many=True, read_only=True)
    
    # Cloudinary: Will automatically return the full image URL
    image = serializers.ImageField()
    min_price = serializers.SerializerMethodField()
    max_price = serializers.SerializerMethodField()
    available_tickets = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'image', 'description', 'category', 'organizer',
            'date', 'time', 'location', 'available_tickets', 'status',
            'ticket_tiers','min_price',
            'max_price', 'latitude', 'longitude', 'created_at'
        ]

    def get_min_price(self, obj):
        """Get minimum ticket price"""
        prices = [tier.price for tier in obj.ticket_tiers.all()]
        return min(prices) if prices else None
    
    def get_max_price(self, obj):
        """Get maximum ticket price"""
        prices = [tier.price for tier in obj.ticket_tiers.all()]
        return max(prices) if prices else None
    
    def get_available_tickets(self, obj):
        """Get total available tickets across all tiers"""
        return sum(tier.availableQuantity for tier in obj.ticket_tiers.all())    

class EventCreateSerializer(serializers.ModelSerializer):
    # WRITE MODE: Accept ID for category, File for image
    
    # Validation: Ensure the category ID exists
    
    class Meta:
        model = Event
        fields = [
            'id', 'image', 'category', 'title', 'description', 
            'date','startDateTime','endDateTime', 'time', 'location', 'latitude', 'longitude', 
            'available_tickets', 'status'
        ]
        # Organizer is read_only because we will set it automatically from request.user in the View
        read_only_fields = ['organizer', 'created_at', 'updated_at']

    # OPTIONAL: Use the ListSerializer for the response
    # This ensures that after a user creates an event, they get back the nice nested JSON 
    # instead of just IDs.
    def to_representation(self, instance):
        serializer = EventListSerializer(instance, context=self.context)
        return serializer.data        
    

