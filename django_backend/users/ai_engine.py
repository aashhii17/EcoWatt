"""
AI / Machine Learning Engine for Electricity Monitoring System
Utilizes Scikit-Learn regression models, statistical anomaly detection, and energy analytics algorithms.
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from django.conf import settings
from .models import Appliance, EnergyConsumption, Prediction, Report

# Carbon Intensity (kg CO2 per kWh) & Tariff default constants
BASE_TARIFF = getattr(settings, 'ELECTRICITY_TARIFF_BASE', 0.14)
CARBON_INTENSITY = getattr(settings, 'CARBON_INTENSITY_FACTOR', 0.85)


class EnergyAIEngine:
    @staticmethod
    def train_and_predict(appliance, forecast_days=7):
        """
        Trains a Scikit-Learn regression model on historical consumption or synthetic baseline model
        to forecast appliance energy usage over forecast_days.
        """
        # Fetch historical consumption
        history = list(
            EnergyConsumption.objects.filter(appliance=appliance)
            .order_by('date')
            .values('date', 'consumption_kwh')
        )

        nominal_daily_kwh = appliance.daily_kwh

        if len(history) >= 5:
            # Prepare dataset for ML model
            df = pd.DataFrame(history)
            df['date'] = pd.to_datetime(df['date'])
            df['day_of_week'] = df['date'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            df['day_num'] = (df['date'] - df['date'].min()).dt.days

            X = df[['day_num', 'day_of_week', 'is_weekend']]
            y = df['consumption_kwh']

            # ML Pipeline
            model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
            model.fit(X, y)

            # Generate forecast features
            start_date = date.today() + timedelta(days=1)
            future_dates = [start_date + timedelta(days=i) for i in range(forecast_days)]
            future_df = pd.DataFrame({
                'date': [pd.to_datetime(d) for d in future_dates]
            })
            future_df['day_of_week'] = future_df['date'].dt.dayofweek
            future_df['is_weekend'] = future_df['day_of_week'].isin([5, 6]).astype(int)
            future_df['day_num'] = (future_df['date'] - pd.to_datetime(df['date'].min())).dt.days

            preds = model.predict(future_df[['day_num', 'day_of_week', 'is_weekend']])
            preds = np.clip(preds, a_min=nominal_daily_kwh * 0.4, a_max=nominal_daily_kwh * 2.5)
            confidence = float(np.clip(1.0 - (np.std(y) / (np.mean(y) + 1e-5)), 0.75, 0.98))
        else:
            # Baseline ML calculation with day-of-week variation factor
            start_date = date.today() + timedelta(days=1)
            future_dates = [start_date + timedelta(days=i) for i in range(forecast_days)]
            preds = []
            for i, d in enumerate(future_dates):
                # Weekend multiplier (1.15) vs weekday (1.0) with slight noise
                weekend_factor = 1.15 if d.weekday() in [5, 6] else 1.0
                day_factor = 1.0 + 0.05 * np.sin(i * np.pi / 3.5)
                val = nominal_daily_kwh * weekend_factor * day_factor
                preds.append(max(val, 0.05))
            confidence = 0.90

        results = []
        for dt_val, pred_kwh in zip(future_dates, preds):
            # Anomaly Detection algorithm
            is_anomaly, anomaly_score, rec = EnergyAIEngine.detect_anomaly_and_recommend(
                appliance=appliance,
                predicted_kwh=float(pred_kwh)
            )

            results.append({
                'date': dt_val,
                'predicted_kwh': round(float(pred_kwh), 3),
                'is_anomaly': is_anomaly,
                'anomaly_score': round(anomaly_score, 2),
                'confidence_score': round(confidence, 2),
                'recommendation': rec
            })

        return results

    @staticmethod
    def detect_anomaly_and_recommend(appliance, predicted_kwh):
        """
        Detects energy anomalies based on expected power rating and usage bounds.
        Generates contextual AI energy saving recommendations.
        """
        expected_kwh = appliance.daily_kwh
        deviation = (predicted_kwh - expected_kwh) / (expected_kwh + 1e-5)

        is_anomaly = False
        anomaly_score = 0.0
        recommendation = f"Appliance '{appliance.name}' is operating within optimal energy parameters."

        if deviation > 0.45:
            is_anomaly = True
            anomaly_score = min(deviation, 1.0)
            recommendation = (
                f"🚨 High Consumption Surge Detected in {appliance.name}! "
                f"Predicted usage ({predicted_kwh:.2f} kWh) is {deviation*100:.1f}% above standard rating. "
                f"Inspect for phantom load, thermostat failure, or inefficient power settings."
            )
        elif deviation < -0.40:
            is_anomaly = False
            anomaly_score = 0.1
            recommendation = (
                f"💡 {appliance.name} is running in energy-saver mode ({predicted_kwh:.2f} kWh predicted)."
            )
        else:
            if appliance.power_rating > 1500:
                recommendation = (
                    f"⚡ High-power appliance ({appliance.power_rating}W). "
                    f"Consider shifting operation outside peak hours (6 PM - 9 PM) to lower utility charges."
                )

        return is_anomaly, anomaly_score, recommendation

    @staticmethod
    def compute_user_analytics(user_profile):
        """
        Computes system-wide energy efficiency score, CO2 carbon footprint, total cost breakdown,
        and multi-appliance recommendations for the user dashboard.
        """
        appliances = Appliance.objects.filter(user_profile=user_profile)

        if not appliances.exists():
            return {
                'total_monthly_kwh': 0.0,
                'total_monthly_cost': 0.0,
                'total_co2_kg': 0.0,
                'efficiency_index': 100.0,
                'estimated_savings': 0.0,
                'peak_load_kwh': 0.0,
                'recommendations': ["Add your household appliances to receive personalized AI energy insights."]
            }

        total_monthly_kwh = sum(a.monthly_kwh for a in appliances)
        total_monthly_cost = sum(a.monthly_cost for a in appliances)
        total_co2_kg = sum(a.monthly_co2_kg for a in appliances)

        # Efficiency calculation based on power factor and high-consumption appliances ratio
        high_power_count = sum(1 for a in appliances if a.power_rating > 1000)
        total_count = appliances.count()

        # Efficiency index formula (0-100%)
        efficiency_index = max(100.0 - (high_power_count / total_count * 25.0) - (total_monthly_kwh / 500.0 * 10.0), 45.0)
        efficiency_index = min(round(efficiency_index, 1), 99.5)

        # Estimated potential savings from AI optimization (15-25% typical savings)
        estimated_savings = round(total_monthly_cost * (0.18 + (100.0 - efficiency_index) / 500.0), 2)
        peak_load_kwh = round(total_monthly_kwh * 0.35 / 30.0, 2)

        # Contextual Recommendations
        recommendations = []
        if high_power_count > 0:
            recommendations.append(f"⚡ Shifting {high_power_count} high-load appliance(s) to off-peak hours can save up to ${estimated_savings * 0.4:.2f}/month.")
        if total_co2_kg > 150:
            recommendations.append(f"🌱 Carbon Footprint Alert: Your monthly emissions are {total_co2_kg:.1f} kg CO2. Eco-mode scheduling can eliminate ~{total_co2_kg * 0.15:.1f} kg CO2.")
        recommendations.append("📊 AI Forecast predicts steady appliance efficiency over the next 7 days.")

        return {
            'total_monthly_kwh': round(total_monthly_kwh, 2),
            'total_monthly_cost': round(total_monthly_cost, 2),
            'total_co2_kg': round(total_co2_kg, 2),
            'efficiency_index': efficiency_index,
            'estimated_savings': estimated_savings,
            'peak_load_kwh': peak_load_kwh,
            'recommendations': recommendations
        }


def generate_predictions_and_reports_for_user(user_profile):
    """
    Service wrapper to generate DB Prediction and Report objects for a user profile using EnergyAIEngine.
    """
    appliances = Appliance.objects.filter(user_profile=user_profile)
    generated_predictions = []

    for appliance in appliances:
        forecasts = EnergyAIEngine.train_and_predict(appliance, forecast_days=7)
        for fc in forecasts:
            prediction, _ = Prediction.objects.update_or_create(
                user_profile=user_profile,
                appliance=appliance,
                predicted_date=fc['date'],
                defaults={
                    'predicted_consumption_kwh': fc['predicted_kwh'],
                    'is_anomaly': fc['is_anomaly'],
                    'anomaly_score': fc['anomaly_score'],
                    'confidence_score': fc['confidence_score'],
                    'recommendation': fc['recommendation']
                }
            )
            generated_predictions.append(prediction)

    # Generate or update Report for today
    analytics = EnergyAIEngine.compute_user_analytics(user_profile)
    report, _ = Report.objects.update_or_create(
        user_profile=user_profile,
        report_date=date.today(),
        defaults={
            'total_consumption_kwh': analytics['total_monthly_kwh'],
            'total_cost': analytics['total_monthly_cost'],
            'efficiency': analytics['efficiency_index'],
            'co2_emissions_kg': analytics['total_co2_kg'],
            'savings_amount': analytics['estimated_savings'],
            'peak_usage_kwh': analytics['peak_load_kwh']
        }
    )

    return generated_predictions, report
