from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import UserProfile, Appliance, EnergyConsumption, Prediction, Report
from .serializers import (
    UserProfileSerializer, ApplianceSerializer, EnergyConsumptionSerializer, 
    PredictionSerializer, ReportSerializer
)
from .ai_engine import EnergyAIEngine, generate_predictions_and_reports_for_user

class ApplianceViewSet(viewsets.ModelViewSet):
    serializer_class = ApplianceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Appliance.objects.filter(user_profile__user=self.request.user)

    def perform_create(self, serializer):
        user_profile = UserProfile.objects.get(user=self.request.user)
        serializer.save(user_profile=user_profile)

class ConsumptionViewSet(viewsets.ModelViewSet):
    serializer_class = EnergyConsumptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EnergyConsumption.objects.filter(appliance__user_profile__user=self.request.user)

class PredictionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PredictionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Prediction.objects.filter(user_profile__user=self.request.user).order_by('-predicted_date')

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_analytics_api(request):
    """
    Returns full system summary, AI insights, carbon emissions, and trend forecasts in JSON format.
    """
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return Response({'error': 'UserProfile not found'}, status=status.HTTP_404_NOT_FOUND)

    analytics = EnergyAIEngine.compute_user_analytics(user_profile)
    appliances = Appliance.objects.filter(user_profile=user_profile)
    appliance_serializer = ApplianceSerializer(appliances, many=True)
    predictions = Prediction.objects.filter(user_profile=user_profile).order_by('-predicted_date')[:7]
    prediction_serializer = PredictionSerializer(predictions, many=True)

    return Response({
        'user': {
            'full_name': user_profile.full_name,
            'email': request.user.email,
            'contact_number': user_profile.contact_number,
        },
        'analytics': analytics,
        'appliances': appliance_serializer.data,
        'recent_predictions': prediction_serializer.data,
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def trigger_predictions_api(request):
    """
    Triggers execution of the AI Machine Learning Engine to refresh predictions & reports.
    """
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return Response({'error': 'UserProfile not found'}, status=status.HTTP_404_NOT_FOUND)

    preds, report = generate_predictions_and_reports_for_user(user_profile)
    return Response({
        'status': 'success',
        'predictions_generated': len(preds),
        'report_id': report.id
    })
