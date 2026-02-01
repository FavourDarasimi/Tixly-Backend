from rest_framework import serializers
from .models import Event,TicketTier,Coupon,EventDay,Speaker,Schedule
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
    # duration_days = serializers.SerializerMethodField()
    # is_currently_happening = serializers.SerializerMethodField()
    # has_schedule = serializers.SerializerMethodField()
    # schedule_count = serializers.SerializerMethodField()
    
    

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'image',"short_description", 'description', 'category', 'organizer',
            'location', 'startDateTime', 'endDateTime', 
            'is_multi_day', 
            'status', 'ticket_tiers', 
            'latitude', 'longitude', 
            'created_at',
            'min_price', 'max_price', 'available_tickets'
        ]
        # 'has_schedule', 'schedule_count','min_price', 'max_price','is_currently_happening', 'available_tickets','duration_days',

    def get_min_price(self, obj):
        prices = [tier.price for tier in obj.ticket_tiers.all()]
        return min(prices) if prices else None
    
    def get_max_price(self, obj):
        prices = [tier.price for tier in obj.ticket_tiers.all()]
        return max(prices) if prices else None
    
    def get_available_tickets(self, obj):
        return sum(tier.available_tickets for tier in obj.ticket_tiers.all())  

    # def get_duration_days(self, obj):
    #     return obj.get_duration_days()
    
    # def get_is_currently_happening(self, obj):
    #     return obj.is_currently_happening()
    
    # def get_has_schedule(self, obj):
    #     """Check if event has any schedule items"""
    #     return obj.schedules.exists()
    
    # def get_schedule_count(self, obj):
    #     """Count of schedule items"""
    #     return obj.schedules.count()

    
        




class EventCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Event
        fields = [
            'id', 'image', 'category', 'title',"short_description", 'description', 
            'startDateTime','endDateTime',  'location', 'latitude', 'longitude', 
            'available_tickets', 'status'
        ]
        read_only_fields = ['organizer', 'created_at', 'updated_at']

    def to_representation(self, instance):
        serializer = EventListSerializer(instance, context=self.context)
        return serializer.data     


class EventDaySerializer(serializers.ModelSerializer):
    event = EventListSerializer(read_only=True)
    
    class Meta:
        model = EventDay
        fields = ["id","event","dayNumber","date","startTime","endTime","title","description"]
        read_only_fields = ['event']
     
    
class SpeakerSerializer(serializers.ModelSerializer):
    """Serializer for Speaker model"""
    profile_image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Speaker
        fields = [
            'id', 'name', 'title',  'profile_image',
            'email', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ScheduleSerializer(serializers.ModelSerializer):
    """Serializer for Schedule with speaker details"""
    speakers = SpeakerSerializer(many=True, read_only=True)
    speaker_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="List of speaker UUIDs to assign to this schedule"
    )
    duration_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = Schedule
        fields = [
            'id', 'title', 'description', 'session_type',
            'start_time', 'end_time', 'date',
            'speakers', 'speaker_ids', 'order', 
             'duration_minutes', 'event_day',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_duration_minutes(self, obj):
        """Calculate duration in minutes"""
        if obj.start_time and obj.end_time:
            from datetime import datetime, timedelta
            start = datetime.combine(datetime.today(), obj.start_time)
            end = datetime.combine(datetime.today(), obj.end_time)
            duration = end - start
            return int(duration.total_seconds() / 60)
        return None
    
    def validate(self, data):
        """Validate schedule times and dates"""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError(
                "End time must be after start time"
            )
        
        return data
    
        return schedule
    
    def update(self, instance, validated_data):
        """Update schedule with speakers"""
        speaker_ids = validated_data.pop('speaker_ids', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update speakers if provided
        if speaker_ids is not None:
            speakers = Speaker.objects.filter(id__in=speaker_ids)
            instance.speakers.set(speakers)
        
        return instance

class SimpleEventDaySerializer(serializers.ModelSerializer):
    """EventDay serializer without neseted event to avoid circular queries"""
    class Meta:
        model = EventDay
        fields = ["id","dayNumber","date","startTime","endTime","title","description"]


class ScheduleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for schedule listings"""
    speakers =SpeakerSerializer(many=True, read_only=True)
    event_day = SimpleEventDaySerializer()
    
    class Meta:
        model = Schedule
        fields = [
            'id', 'title', 'session_type', 'start_time','description','event_day',
            'end_time',  'speakers',
             'order'
        ]
    


class EventDayWithScheduleSerializer(serializers.ModelSerializer):
    """EventDay serializer with nested schedules"""
    schedules = ScheduleListSerializer(many=True, read_only=True)
    
    class Meta:
        model = EventDay
        fields = [
            'id', 'dayNumber', 'date', 'startTime', 'endTime',
            'title', 'description', 'schedules', 'createdAt', 'updatedAt'
        ]

class EventDetailSerializer(EventListSerializer):
    """Extended serializer with full schedule details"""
    event_days = EventDayWithScheduleSerializer(many=True, read_only=True)
    # schedules = ScheduleListSerializer(many=True, read_only=True) # REMOVED: Redundant
    speakers = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    
    class Meta(EventListSerializer.Meta):
        fields = EventListSerializer.Meta.fields + ['event_days', 'speakers', 'is_saved']

    def get_is_saved(self, obj):
        if hasattr(obj, 'is_saved_by_user'):
            return obj.is_saved_by_user
            
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.saved_by.filter(user=user).exists()
        return False

    def get_speakers(self, obj):
        # Optimize: Avoid re-querying by using the pre-fetched schedules
        # which already have speakers pre-fetched
        unique_speakers = {}
        
        for schedule in obj.schedules.all():
            for speaker in schedule.speakers.all():
                if speaker.id not in unique_speakers:
                    unique_speakers[speaker.id] = speaker
                    
        return SpeakerSerializer(unique_speakers.values(), many=True).data

