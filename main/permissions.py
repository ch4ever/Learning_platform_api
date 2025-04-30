from rest_framework import permissions

class RolePermission(permissions.BasePermission):
    allowed_roles=[]
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated() and getattr(request.user, 'role', None) in self.allowed_roles
        )

class StudentOrAbove(RolePermission):
    allowed_roles=['student','teacher','staff']

class TeacherOrAbove(RolePermission):
    allowed_roles=['teacher','staff']
    def has_object_permission(self, request,obj,view):
        return obj.owner == request.user

class Staff(RolePermission):
    allowed_roles = ['staff']