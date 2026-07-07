from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Appliance, EnergyConsumption, Prediction, Report

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'full_name', 'contact_number', 'physical_address', 'created_at']

class ApplianceSerializer(serializers.ModelSerializer):
    daily_kwh = serializers.ReadOnlyField()
    monthly_kwh = serializers.ReadOnlyField()
    monthly_cost = serializers.ReadOnlyField()
    monthly_co2_kg = serializers.ReadOnlyField()

    class Meta:
        model = Appliance
        fields = [
            'id', 'name', 'power_rating', 'quantity', 
            'days_used_per_week', 'usage_time', 
            'daily_kwh', 'monthly_kwh', 'monthly_cost', 'monthly_co2_kg', 'created_at'
        ]

class EnergyConsumptionSerializer(serializers.ModelSerializer):
    appliance_name = serializers.ReadOnlyField(source='appliance.name')

    class Meta:
        model = EnergyConsumption
        fields = ['id', 'appliance', 'appliance_name', 'date', 'consumption_kwh', 'recorded_at']

class PredictionSerializer(serializers.ModelSerializer):
    appliance_name = serializers.ReadOnlyField(source='appliance.name')

    class Meta:
        model = Prediction
        fields = [
            'id', 'appliance', 'appliance_name', 'predicted_date', 
            'predicted_consumption_kwh', 'is_anomaly', 'anomaly_score', 
            'confidence_score', 'recommendation', 'created_at'
        ]

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            'id', 'report_date', 'total_consumption_kwh', 'total_cost', 
            'efficiency', 'co2_emissions_kg', 'savings_amount', 'peak_usage_kwh', 'created_at'
        ]
