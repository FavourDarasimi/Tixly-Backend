from django.urls import path
from .views import CreateEvent,UpdateEvent,DeleteEvent,OrganizerEvents,EventAttendees,CreateTicketTiers,UpdateTicketTier,DeleteTicketTier

urlpatterns = [
    path("create/event/",CreateEvent.as_view(),name="create-event"),
    path("update/event/<int:pk>/",UpdateEvent.as_view(),name="update-event"),
    path("delete/event/<int:pk>/",DeleteEvent.as_view(),name="delete-event"),
    path("events/",OrganizerEvents.as_view(),name="events"),
    path("events/<int:pk>/attendees/",EventAttendees.as_view(),name="event-attendees"),
    path("events/ticket-tiers/update/<int:pk>/",UpdateTicketTier.as_view(),name="event-ticket-tiers"),
    path("events/ticket-tiers/delete/<int:pk>/",DeleteTicketTier.as_view(),name="event-ticket-tiers"),
]