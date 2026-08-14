from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied, NotAuthenticated

class IsSuperAdminUser(permissions.BasePermission):
    """
    Allows access only to superadmin users.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated("No se entraron las credenciales correctas.")
        if not request.user.is_superuser:
            raise PermissionDenied("No tienes permiso para realizar esta operación.")
        return True