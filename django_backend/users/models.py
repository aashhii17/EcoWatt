from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=20, unique=True, db_index=True)
    physical_address = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.full_name} ({self.contact_number})"

class Appliance(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='appliances')
    name = models.CharField(max_length=255)
    power_rating = models.FloatField(help_text="Power rating in watts")
    quantity = models.PositiveIntegerField(default=1)
    days_used_per_week = models.PositiveIntegerField(default=7, help_text="Number of days appliance is used per week")
    usage_time = models.FloatField(default=1.0, help_text="Daily usage time in hours")
    created_at = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return f"{self.name} (Qty: {self.quantity}, {self.power_rating}W)"

    @property
    def daily_kwh(self):
        """Calculates expected daily energy consumption in kWh."""
        return (self.power_rating * self.quantity * self.usage_time) / 1000.0

    @property
    def monthly_kwh(self):
        """Calculates expected monthly energy consumption in kWh."""
        return self.daily_kwh * (self.days_used_per_week * 4.33 / 7.0)

    @property
    def monthly_cost(self):
        """Calculates estimated monthly cost based on base tariff."""
        base_tariff = float(getattr(settings, 'ELECTRICITY_TARIFF_BASE', 0.14))
        return self.monthly_kwh * base_tariff

    @property
    def monthly_co2_kg(self):
        """Calculates estimated CO2 emissions in kg."""
        intensity = float(getattr(settings, 'CARBON_INTENSITY_FACTOR', 0.85))
        return self.monthly_kwh * intensity

class EnergyConsumption(models.Model):
    appliance = models.ForeignKey(Appliance, on_delete=models.CASCADE, related_name='consumptions')
    date = models.DateField(db_index=True)
    consumption_kwh = models.FloatField(help_text="Energy consumption in kWh")
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['appliance', 'date']),
        ]

    def __str__(self):
        return f"{self.appliance.name} - {self.date} : {self.consumption_kwh} kWh"

class Prediction(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='predictions')
    appliance = models.ForeignKey(Appliance, on_delete=models.CASCADE, related_name='predictions')
    predicted_date = models.DateField(db_index=True)
    predicted_consumption_kwh = models.FloatField(help_text="Predicted energy consumption in kWh")
    is_anomaly = models.BooleanField(default=False)
    anomaly_score = models.FloatField(default=0.0, help_text="Anomaly severity index (0.0 to 1.0)")
    confidence_score = models.FloatField(default=0.95, help_text="AI Model Confidence Score")
    recommendation = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-predicted_date']

    def __str__(self):
        return f"Prediction for {self.appliance.name} on {self.predicted_date}: {self.predicted_consumption_kwh} kWh"

class Report(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='reports')
    report_date = models.DateField(db_index=True)
    total_consumption_kwh = models.FloatField()
    total_cost = models.FloatField()
    efficiency = models.FloatField(help_text="Efficiency percentage (0-100)")
    co2_emissions_kg = models.FloatField(default=0.0, help_text="Carbon emissions in kg")
    savings_amount = models.FloatField(default=0.0, help_text="Estimated savings in currency")
    peak_usage_kwh = models.FloatField(default=0.0)
    created_at = models.DateTimeField(default=timezone.now)


    class Meta:
        ordering = ['-report_date']

    def __str__(self):
        return f"Report for {self.user_profile.full_name} on {self.report_date}"
