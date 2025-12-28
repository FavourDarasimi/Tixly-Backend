from django.contrib import admin
from .models import Event,EventDay,TicketTier,Coupon 

admin.site.register(Event)
admin.site.register(EventDay)
admin.site.register(TicketTier)
admin.site.register(Coupon)
# Register your models here.
