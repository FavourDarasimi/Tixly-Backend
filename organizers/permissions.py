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


    message = "You don't have perission to perform this action."

    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated
            and obj.organizer == request.user
        )