# services.py
# Business logic services delegating to the Energy AI Engine.

from .ai_engine import EnergyAIEngine, generate_predictions_and_reports_for_user

def generate_dummy_prediction(user_profile):
    """
    Service function for backward compatibility. Now invokes the full ML Engine.
    """
    preds, report = generate_predictions_and_reports_for_user(user_profile)
    return preds
