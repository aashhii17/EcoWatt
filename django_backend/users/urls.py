from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, views_profile, api_views

router = DefaultRouter()
router.register(r'appliances', api_views.ApplianceViewSet, basename='api-appliances')
router.register(r'consumption', api_views.ConsumptionViewSet, basename='api-consumption')
router.register(r'predictions', api_views.PredictionViewSet, basename='api-predictions')

urlpatterns = [
    # Authentication & Registration
    path('', views.user_login, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('signup/add_appliances/', views.add_appliances_view, name='signup_add_appliances'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    path('register/', views.register_user, name='register_api'),

    # Dashboard & Appliance Management
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('add_appliances/', views.add_appliances_view, name='add_appliances'),
    path('add_appliances', views.add_appliances_view, name='add_appliances_no_slash'),
    path('remove_appliance/<int:appliance_id>/', views.remove_appliance_view, name='remove_appliance'),
    path('appliances/', views.appliances_list_view, name='appliances_list'),
    path('consumption/<int:appliance_id>/', views.consumption_view, name='consumption'),

    # Analytics & AI Predictions
    path('predictions/', views.predictions_view, name='predictions'),
    path('generate_predictions/', views.generate_predictions_view, name='generate_predictions'),
    path('reports/', views.reports_view, name='reports'),

    # Admin Management Portal
    path('admin_dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin_dashboard/export/', views.export_user_data_to_excel, name='export_user_data'),
    path('admin_remove_appliance/<int:appliance_id>/', views.admin_remove_appliance_view, name='admin_remove_appliance'),
    path('admin_add_appliance/', views.admin_add_appliance_view, name='admin_add_appliance'),
    path('admin_remove_user/<int:user_profile_id>/', views.admin_remove_user_view, name='admin_remove_user'),

    # User Profile & Security
    path('profile/', views_profile.profile_view, name='profile'),
    path('delete_account/', views_profile.delete_account_view, name='delete_account'),
    path('switch_account/', views_profile.switch_account_view, name='switch_account'),

    # Django REST Framework API Endpoints
    path('api/v1/', include(router.urls)),
    path('api/v1/dashboard-summary/', api_views.dashboard_analytics_api, name='api_dashboard_summary'),
    path('api/v1/trigger-predictions/', api_views.trigger_predictions_api, name='api_trigger_predictions'),
]
