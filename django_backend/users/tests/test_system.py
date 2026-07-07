from datetime import date
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from users.models import UserProfile, Appliance, EnergyConsumption, Prediction, Report
from users.ai_engine import EnergyAIEngine, generate_predictions_and_reports_for_user


class ElectricityMonitoringSystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "SecurePass123!"
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password=self.password
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            full_name="John Doe",
            contact_number="9876543210",
            physical_address="123 Smart Grid Lane"
        )
        self.appliance1 = Appliance.objects.create(
            user_profile=self.profile,
            name="Air Conditioner",
            power_rating=1500.0,
            quantity=1,
            days_used_per_week=7,
            usage_time=4.0
        )
        self.appliance2 = Appliance.objects.create(
            user_profile=self.profile,
            name="LED TV",
            power_rating=100.0,
            quantity=2,
            days_used_per_week=7,
            usage_time=5.0
        )

    def test_appliance_calculated_properties(self):
        """Test daily, monthly kWh, cost, and carbon footprint calculations."""
        # AC: (1500 * 1 * 4) / 1000 = 6.0 kWh daily
        self.assertEqual(self.appliance1.daily_kwh, 6.0)
        # AC Monthly: 6.0 * 4.33 = 25.98 kWh
        self.assertAlmostEqual(self.appliance1.monthly_kwh, 25.98, places=2)
        self.assertGreater(self.appliance1.monthly_cost, 0.0)
        self.assertGreater(self.appliance1.monthly_co2_kg, 0.0)

    def test_ai_engine_forecasting_and_analytics(self):
        """Test Machine Learning forecasting engine and system analytics."""
        analytics = EnergyAIEngine.compute_user_analytics(self.profile)
        self.assertIn('total_monthly_kwh', analytics)
        self.assertGreater(analytics['total_monthly_kwh'], 0.0)
        self.assertGreaterEqual(analytics['efficiency_index'], 45.0)

        forecasts = EnergyAIEngine.train_and_predict(self.appliance1, forecast_days=7)
        self.assertEqual(len(forecasts), 7)
        self.assertIn('predicted_kwh', forecasts[0])
        self.assertIn('recommendation', forecasts[0])

    def test_prediction_generation_service(self):
        """Test auto generation of Predictions and Report models."""
        preds, report = generate_predictions_and_reports_for_user(self.profile)
        self.assertGreater(len(preds), 0)
        self.assertIsNotNone(report)
        self.assertEqual(report.user_profile, self.profile)

    def test_user_authentication_flow(self):
        """Test login and dashboard access."""
        login_success = self.client.login(username="testuser@example.com", password=self.password)
        self.assertTrue(login_success)

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Air Conditioner")

    def test_add_appliance_flow(self):
        """Test adding appliances via web view."""
        self.client.login(username="testuser@example.com", password=self.password)
        response = self.client.post(reverse('add_appliances'), {
            'name[]': ['Refrigerator'],
            'brand[]': ['Samsung'],
            'model[]': ['Inverter'],
            'usage_time[]': ['24'],
            'quantity[]': ['1'],
            'days_used_per_week[]': ['7'],
            'power_rating[]': ['200']
        })
        self.assertEqual(response.status_code, 302)  # Redirects to dashboard
        self.assertTrue(Appliance.objects.filter(user_profile=self.profile, name__icontains="Refrigerator").exists())

    def test_rest_api_dashboard_analytics(self):
        """Test REST API endpoint for dashboard summary."""
        self.client.login(username="testuser@example.com", password=self.password)
        response = self.client.get(reverse('api_dashboard_summary'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('analytics', data)
        self.assertIn('appliances', data)
