from django.contrib import admin
from .models import Event,EventDay,TicketTier,Coupon,Speaker,Schedule 

admin.site.register(Event)
admin.site.register(EventDay)
admin.site.register(Speaker)
admin.site.register(Schedule)
admin.site.register(TicketTier)
admin.site.register(Coupon)
# Register your models here.
