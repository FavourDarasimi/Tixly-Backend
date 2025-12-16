from rest_framework import serializers
from .models import Category,Event,TicketTier,Coupon
from accounts.models import User


class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

# --- Helper: TicketTier Serializer ---
class TicketTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketTier
        fields = '__all__'
        # event is optional here if you create tickets via a nested route
        # e.g., POST /events/5/tickets/
        extra_kwargs = {'event': {'read_only': True}}


class EventListSerializer(serializers.ModelSerializer):
    # READ MODE: Use nested serializers to show full object details
    category = CategorySerializer(read_only=True)
    organizer = UserPublicSerializer(read_only=True)
    
    # Reverse relationship: Show all tickets associated with this event
    # Note: 'ticket_types' matches the related_name in your TicketTier model
    ticket_types = TicketTierSerializer(many=True, read_only=True)
    
    # Cloudinary: Will automatically return the full image URL
    image = serializers.ImageField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'image', 'description', 'category', 'organizer',
            'date', 'time', 'location', 'available_tickets', 'status',
            'ticket_types', 'latitude', 'longitude', 'created_at'
        ]

class EventCreateSerializer(serializers.ModelSerializer):
    # WRITE MODE: Accept ID for category, File for image
    
    # Validation: Ensure the category ID exists
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    
    class Meta:
        model = Event
        fields = [
            'id', 'image', 'category', 'title', 'description', 
            'date', 'time', 'location', 'latitude', 'longitude', 
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