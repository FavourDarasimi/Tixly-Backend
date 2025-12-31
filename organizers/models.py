
from django.utils import timezone
import uuid
from django.db import models
from cloudinary.models import CloudinaryField
from django.contrib.auth import get_user_model
user = get_user_model()



class Event(models.Model):
    CATEGORY_CHOICES = (
        ('music', 'Music'),
        ('sports', 'Sports'),
        ('conference', 'Conference'),
        ('workshop', 'Workshop'),
        ('festival', 'Festival'),
        ('theater', 'Theater'),
        ('tech', 'Tech'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    image = CloudinaryField('image')
    category = models.CharField(choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=255)
    short_description = models.CharField(max_length=255)
    description = models.TextField()
    is_multi_day = models.BooleanField(default=False, help_text="Auto-calculated if event spans multiple days")
    startDateTime = models.DateTimeField(null=True, blank=True)
    endDateTime = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    available_tickets = models.IntegerField()
    organizer = models.ForeignKey(user, on_delete=models.CASCADE, related_name='events')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    

    def save(self, *args, **kwargs):
        if self.startDateTime and self.endDateTime:
            self.isMultiDay = self.startDateTime.date() != self.endDateTime.date()
        super().save(*args, **kwargs)
    
    def get_duration_days(self):
        if self.startDateTime and self.endDateTime:
            delta = self.endDateTime.date() - self.startDateTime.date()
            return delta.days + 1 
        return 1
    
    def is_happening_on_date(self, check_date):
        return self.startDateTime.date() <= check_date <= self.endDateTime.date()
    
    def is_currently_happening(self):
        now = timezone.now()
        return self.startDateTime <= now <= self.endDateTime
    
    
    

class EventDay(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_days')
    
    dayNumber = models.IntegerField(help_text="Day 1, Day 2, etc.")
    date = models.DateField()
    startTime = models.TimeField()
    endTime = models.TimeField()
    
    title = models.CharField(max_length=255, help_text="e.g., 'Day 1: Keynote Sessions'")
    description = models.TextField(blank=True)
    
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date', 'startTime']
        unique_together = ['event', 'dayNumber']
    
    def __str__(self):
        return f"{self.event.title} - Day {self.dayNumber}"



class Speaker(models.Model):
    """Speaker model for event schedules"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255, help_text="Job title or role")
    profile_image = CloudinaryField('speaker_image', null=True, blank=True)
    email = models.EmailField(blank=True)
    

    organizer = models.ForeignKey(
        user, 
        on_delete=models.CASCADE, 
        related_name='speakers'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['organizer', 'name']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.title}"


class Schedule(models.Model):
    SESSION_TYPES = (
        ('keynote', 'Keynote'),
        ('talk', 'Talk'),
        ('panel', 'Panel Discussion'),
        ('workshop', 'Workshop'),
        ('break', 'Break'),
        ('networking', 'Networking'),
        ('lunch', 'Lunch'),
        ('registration', 'Registration'),
        ('other', 'Other'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        related_name='schedules'
    )
    event_day = models.ForeignKey(
        EventDay, 
        on_delete=models.CASCADE, 
        related_name='schedules',
        null=True,
        blank=True,
        help_text="Optional: Link to specific event day for multi-day events"
    )
    
    # Schedule details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    session_type = models.CharField(
        max_length=20, 
        choices=SESSION_TYPES, 
        default='talk'
    )
    
    # Time details
    start_time = models.TimeField()
    end_time = models.TimeField()
    date = models.DateField(help_text="Date of this schedule item")
    
    
    # Speakers (many-to-many relationship)
    speakers = models.ManyToManyField(
        Speaker,
        related_name='schedules',
        blank=True
    )
    
    # Display order
    order = models.PositiveIntegerField(
        default=0,
        help_text="Order of appearance in schedule"
    )
    
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date', 'start_time', 'order']
        indexes = [
            models.Index(fields=['event', 'date', 'start_time']),
            models.Index(fields=['event_day', 'start_time']),
            
        ]
    
    def __str__(self):
        return f"{self.event.title} - {self.title} ({self.date} {self.start_time})"
    
    def clean(self):
        """Validate that end_time is after start_time"""
        from django.core.exceptions import ValidationError
        
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError('End time must be after start time')
        
        # Validate date is within event date range
        if self.date and self.event:
            event_start = self.event.startDateTime.date()
            event_end = self.event.endDateTime.date()
            
            if not (event_start <= self.date <= event_end):
                raise ValidationError(
                    f'Schedule date must be between event dates '
                    f'({event_start} to {event_end})'
                )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)




class TicketTier(models.Model):
    name = models.CharField(max_length=255)
    short_description = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_tiers')
    total_tickets = models.IntegerField()
    available_tickets = models.IntegerField()
    salesStart = models.DateTimeField()
    saleEnd = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.event.title} - {self.name}'

class Coupon(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='coupons')
    code = models.CharField(max_length=20)
    discount_percentage = models.PositiveIntegerField(default=0) # e.g., 10 for 10% off
    fixed_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) # e.g., remove $5
    
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=100)
    times_used = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.code


# Create your models here.
