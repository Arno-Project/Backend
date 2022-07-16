from django.contrib import admin

# Register your models here.
from accounts import models

admin.site.register(models.User)
admin.site.register(models.CompanyManager)
admin.site.register(models.TechnicalManager)
admin.site.register(models.NormalUser)
admin.site.register(models.ManagerUser)
admin.site.register(models.Customer)
admin.site.register(models.Specialist)