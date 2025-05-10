from rest_framework import permissions
from rest_framework.permissions import BasePermission

#SITE PERMISSIONS
class RolePermission(permissions.BasePermission):
    allowed_roles=[]
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and getattr(request.user, 'role', None) in self.allowed_roles
        )

class StudentOrAbove(RolePermission):
    allowed_roles=['student','teacher','staff']

class TeacherOrAbove(RolePermission):
    allowed_roles=['teacher','staff']
    def has_object_permission(self, request,obj,view):
        return obj.owner == request.user

class VerifiedTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.status == 'approved'

class Staff(RolePermission):
    allowed_roles = ['staff']


#COURSE PERMISSIONS
class CourseRolePermissions(permissions.BasePermission):
    allowed_roles = []

    def has_object_permission(self, request, view,obj):
        user_roles =obj.course_roles.filter(user=request.user).values_list('role',flat=True)
        return any(role in self.allowed_roles for role in user_roles) or request.user.role in ['staff'] or request.user.is_superuser


class Student(CourseRolePermissions):
    allowed_roles = ['student','co_lecturer','lecturer']

class CoLecturerOrAbove(CourseRolePermissions):
    allowed_roles = ['lecturer','co_lecturer']

class LecturerOrAbove(CourseRolePermissions):
    allowed_roles = ['lecturer']