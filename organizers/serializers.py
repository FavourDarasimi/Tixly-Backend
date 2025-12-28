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
    ticket_tiers = TicketTierSerializer(many=True, read_only=True)
    image = serializers.ImageField()
    min_price = serializers.SerializerMethodField()
    max_price = serializers.SerializerMethodField()
    available_tickets = serializers.SerializerMethodField()
    duration_days = serializers.SerializerMethodField()
    is_currently_happening = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'image', 'description', 'category', 'organizer',
         'location','startDateTime',
            'endDateTime',
            'duration_days',
            'is_multi_day',
            'is_currently_happening', 'available_tickets', 'status',
            'ticket_tiers','min_price',
            'max_price', 'latitude', 'longitude', 'created_at'
        ]

    def get_min_price(self, obj):
   
        prices = [tier.price for tier in obj.ticket_tiers.all()]
        return min(prices) if prices else None
    
    def get_max_price(self, obj):

        prices = [tier.price for tier in obj.ticket_tiers.all()]
        return max(prices) if prices else None
    
    def get_available_tickets(self, obj):
 
        return sum(tier.available_tickets for tier in obj.ticket_tiers.all())  


    def get_duration_days(self, obj):
    
        return obj.get_duration_days()
    
    def get_is_currently_happening(self, obj):

        return obj.is_currently_happening()  

class EventCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Event
        fields = [
            'id', 'image', 'category', 'title', 'description', 
            'startDateTime','endDateTime',  'location', 'latitude', 'longitude', 
            'available_tickets', 'status'
        ]
        read_only_fields = ['organizer', 'created_at', 'updated_at']

    def to_representation(self, instance):
        serializer = EventListSerializer(instance, context=self.context)
        return serializer.data        
    

