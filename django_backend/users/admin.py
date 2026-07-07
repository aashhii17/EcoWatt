from django.contrib import admin
from .models import UserProfile, Appliance, EnergyConsumption, Prediction, Report

admin.site.register(UserProfile)
admin.site.register(Appliance)
admin.site.register(EnergyConsumption)
admin.site.register(Prediction)
admin.site.register(Report)
