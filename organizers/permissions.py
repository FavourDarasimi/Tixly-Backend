from rest_framework.permissions import BasePermission



class IsOrganizer(BasePermission):

    message = "Only organizers can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "organizer"
        )
    
class IsEventOrganizer(BasePermission):


    message = "You don't have permission to perform this action."

    def _get_organizer(self, obj):
        # Direct Event (or anything with .organizer)
        organizer = getattr(obj, 'organizer', None)
        if organizer is not None:
            return organizer
        # TicketTier / Schedule / EventDay etc. expose .event.organizer
        event = getattr(obj, 'event', None)
        if event is not None:
            return getattr(event, 'organizer', None)
        return None

    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated
            and self._get_organizer(obj) == request.user
        )