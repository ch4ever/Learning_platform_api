from django.contrib import admin
from .models import *

# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = ('id','username','role','status','is_staff','is_superuser')
    list_filter = ('id','is_staff','is_superuser')
    search_fields = ('username',)
    ordering = ('id',)

admin.site.register(SiteUser,UserAdmin)