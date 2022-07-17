from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Register your models here.
from accounts import models

admin.site.register(models.CompanyManager)
admin.site.register(models.TechnicalManager)
admin.site.register(models.NormalUser)
admin.site.register(models.ManagerUser)
admin.site.register(models.Customer)
admin.site.register(models.Specialist)
admin.site.register(models.Speciality)

@admin.register(models.User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone', 'role')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('email','phone', 'role')}),
    )
