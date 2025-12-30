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
    duration_days = serializers.SerializerMethodField()
    is_currently_happening = serializers.SerializerMethodField()
    has_schedule = serializers.SerializerMethodField()
    schedule_count = serializers.SerializerMethodField()
    
    

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'image',"short_description", 'description', 'category', 'organizer',
            'location', 'startDateTime', 'endDateTime', 'duration_days',
            'is_multi_day', 'is_currently_happening', 'available_tickets',
            'status', 'ticket_tiers', 'min_price', 'max_price',
            'latitude', 'longitude', 'has_schedule', 'schedule_count',
            'created_at'
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
    
    def get_has_schedule(self, obj):
        """Check if event has any schedule items"""
        return obj.schedules.exists()
    
    def get_schedule_count(self, obj):
        """Count of schedule items"""
        return obj.schedules.count()

    
        




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
    
    def create(self, validated_data):
        """Create schedule with speakers"""
        speaker_ids = validated_data.pop('speaker_ids', [])
        schedule = Schedule.objects.create(**validated_data)
        
        if speaker_ids:
            speakers = Speaker.objects.filter(id__in=speaker_ids)
            schedule.speakers.set(speakers)
        
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


class ScheduleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for schedule listings"""
    speaker_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Schedule
        fields = [
            'id', 'title', 'session_type', 'start_time',
            'end_time',  'speaker_names',
             'order'
        ]
    
    def get_speaker_names(self, obj):
        """Get comma-separated speaker names"""
        return ", ".join([speaker.name for speaker in obj.speakers.all()])


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
    schedules = ScheduleListSerializer(many=True, read_only=True)
    speakers = serializers.SerializerMethodField()
    
    class Meta(EventListSerializer.Meta):
        fields = EventListSerializer.Meta.fields + ['event_days', 'schedules','speakers']

    def get_speakers(self,obj):
        speakers_queryset = obj.get_speakers()
        return SpeakerSerializer(speakers_queryset, many=True).data

