import json
import openpyxl
from datetime import date, timedelta
from openpyxl.utils import get_column_letter

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.views.decorators.cache import never_cache

from .models import UserProfile, Appliance, EnergyConsumption, Prediction, Report
from .ai_engine import EnergyAIEngine, generate_predictions_and_reports_for_user


def register_user(request):
    """Secure API endpoint for user registration."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)

        name = data.get('name', '').strip()
        contact = data.get('contact', '').strip()
        email = data.get('email', '').strip()
        address = data.get('address', '').strip()
        password = data.get('password', '').strip()

        if not (name and contact and email and password):
            return JsonResponse({'status': 'error', 'message': 'All required fields must be provided'}, status=400)

        if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
            return JsonResponse({'status': 'error', 'message': 'Email already registered'}, status=400)
        if UserProfile.objects.filter(contact_number=contact).exists():
            return JsonResponse({'status': 'error', 'message': 'Contact number already registered'}, status=400)

        user = User.objects.create_user(username=email, email=email, password=password)
        user_profile = UserProfile.objects.create(
            user=user,
            full_name=name,
            contact_number=contact,
            physical_address=address
        )
        login(request, user)
        return JsonResponse({'status': 'success', 'message': 'User registered successfully'})

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


@staff_member_required
def export_user_data_to_excel(request):
    """Export user profiles and appliance details to Excel spreadsheet."""
    user_profiles = UserProfile.objects.prefetch_related('appliances').select_related('user').all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "User Energy Profiles"

    headers = ['Full Name', 'Contact Number', 'Email', 'Physical Address', 'Total Appliances', 'Monthly kWh', 'Monthly Cost ($)', 'Appliances Detail']
    for col_num, header in enumerate(headers, 1):
        col_letter = get_column_letter(col_num)
        ws[f'{col_letter}1'] = header

    for row_num, profile in enumerate(user_profiles, 2):
        appliances = profile.appliances.all()
        appliances_str = ", ".join([f"{a.name} (Qty: {a.quantity}, {a.power_rating}W)" for a in appliances])
        monthly_kwh = sum(a.monthly_kwh for a in appliances)
        monthly_cost = sum(a.monthly_cost for a in appliances)

        ws[f'A{row_num}'] = profile.full_name
        ws[f'B{row_num}'] = profile.contact_number
        ws[f'C{row_num}'] = profile.user.email
        ws[f'D{row_num}'] = profile.physical_address
        ws[f'E{row_num}'] = len(appliances)
        ws[f'F{row_num}'] = round(monthly_kwh, 2)
        ws[f'G{row_num}'] = round(monthly_cost, 2)
        ws[f'H{row_num}'] = appliances_str

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=energy_user_profiles.xlsx'
    wb.save(response)
    return response


def signup_view(request):
    """User registration page."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        contact_number = request.POST.get('contact_number', '').strip()
        email = request.POST.get('email', '').strip()
        physical_address = request.POST.get('physical_address', '').strip()
        password = request.POST.get('password', '').strip()
        password2 = request.POST.get('password2', '').strip()

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'signup.html')

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return render(request, 'signup.html')

        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, 'signup.html')

        if UserProfile.objects.filter(contact_number=contact_number).exists():
            messages.error(request, "This contact number is already registered.")
            return render(request, 'signup.html')

        user = User.objects.create_user(username=email, email=email, password=password)
        UserProfile.objects.create(
            user=user,
            full_name=full_name,
            contact_number=contact_number,
            physical_address=physical_address
        )
        authenticated_user = authenticate(request, username=email, password=password)
        if authenticated_user:
            login(request, authenticated_user)
            messages.success(request, "Account created successfully! Please add your home appliances.")
            return redirect('add_appliances')

    return render(request, 'signup.html')


def user_login(request):
    """User and Admin login handler."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        contact_no = request.POST.get('contact_no', '').strip()
        password = request.POST.get('password', '').strip()

        if not contact_no or not password:
            messages.error(request, 'Please provide both contact number and password.')
            return render(request, 'login.html')

        # Check by contact_number first
        try:
            user_profile = UserProfile.objects.select_related('user').get(contact_number=contact_no)
            user = authenticate(request, username=user_profile.user.username, password=password)
            if user is not None:
                login(request, user)
                if user.is_staff:
                    return redirect('admin_dashboard')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid password.')
                return render(request, 'login.html')
        except UserProfile.DoesNotExist:
            # Fallback check for standard Django admin user logging in via email/username
            user = authenticate(request, username=contact_no, password=password)
            if user is not None:
                login(request, user)
                if user.is_staff:
                    return redirect('admin_dashboard')
                return redirect('dashboard')
            messages.error(request, 'Account not found for the provided contact number.')

    return render(request, 'login.html')


def forgot_password_view(request):
    """Identify user account by contact number or email for password reset."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        if not identifier:
            messages.error(request, 'Please enter your registered contact number or email address.')
            return render(request, 'forgot_password.html')

        user = None
        # Check by contact_number first
        try:
            profile = UserProfile.objects.select_related('user').get(contact_number=identifier)
            user = profile.user
        except UserProfile.DoesNotExist:
            # Check by email or username
            user_qs = User.objects.filter(email__iexact=identifier) | User.objects.filter(username__iexact=identifier)
            if user_qs.exists():
                user = user_qs.first()

        if user:
            request.session['reset_user_id'] = user.id
            messages.success(request, f"Account found for {user.email or user.username}. Enter your new password.")
            return redirect('reset_password')
        else:
            messages.error(request, 'No account found matching that contact number or email address.')

    return render(request, 'forgot_password.html')


def reset_password_view(request):
    """Set new password for verified account."""
    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please start the password reset process again.')
        return redirect('forgot_password')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Account not found.')
        return redirect('forgot_password')

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not new_password or not confirm_password:
            messages.error(request, 'Please fill in both password fields.')
            return render(request, 'reset_password.html', {'target_user': user})

        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'reset_password.html', {'target_user': user})

        if len(new_password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return render(request, 'reset_password.html', {'target_user': user})

        user.set_password(new_password)
        user.save()
        del request.session['reset_user_id']
        messages.success(request, 'Password reset successfully! Please sign in with your new password.')
        return redirect('login')

    return render(request, 'reset_password.html', {'target_user': user})



@never_cache
@login_required(login_url='login')
def dashboard_view(request):
    """Enterprise AI Dashboard view delivering real-time predictions, energy analytics, and charts."""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        # Auto-create profile if missing for admin user
        user_profile = UserProfile.objects.create(
            user=request.user,
            full_name=request.user.get_full_name() or request.user.username,
            contact_number=f"00000{request.user.id}",
            physical_address="System Administrator Location"
        )

    appliances = Appliance.objects.filter(user_profile=user_profile)

    # Trigger ML Engine predictions refresh if needed
    predictions, report = generate_predictions_and_reports_for_user(user_profile)
    analytics = EnergyAIEngine.compute_user_analytics(user_profile)

    # Prepare chart metrics
    appliances_data = []
    appliance_names = []
    appliance_consumptions = []
    appliance_costs = []
    appliance_co2 = []

    for a in appliances:
        appliance_names.append(a.name)
        appliance_consumptions.append(round(a.monthly_kwh, 2))
        appliance_costs.append(round(a.monthly_cost, 2))
        appliance_co2.append(round(a.monthly_co2_kg, 2))
        appliances_data.append({
            'id': a.id,
            'name': a.name,
            'power_rating': a.power_rating,
            'quantity': a.quantity,
            'days_used_per_week': a.days_used_per_week,
            'usage_time': a.usage_time,
            'consumption': round(a.monthly_kwh, 2),
            'cost': round(a.monthly_cost, 2),
            'co2': round(a.monthly_co2_kg, 2),
        })

    # Fetch recent predictions & anomaly alerts
    recent_predictions = Prediction.objects.filter(user_profile=user_profile).order_by('predicted_date')[:7]
    anomalies = [p for p in recent_predictions if p.is_anomaly or p.anomaly_score > 0.3]

    # Dynamic 7-day forecast series for Chart.js
    forecast_dates = [p.predicted_date.strftime('%b %d') for p in recent_predictions]
    forecast_kwh = [p.predicted_consumption_kwh for p in recent_predictions]

    context = {
        'full_name': user_profile.full_name,
        'contact_number': user_profile.contact_number,
        'email': request.user.email,
        'physical_address': user_profile.physical_address,
        'appliances': appliances,
        'appliances_data': appliances_data,
        'appliances_json': json.dumps(appliances_data),
        'appliance_names': json.dumps(appliance_names),
        'appliance_consumptions': json.dumps(appliance_consumptions),
        'appliance_costs': json.dumps(appliance_costs),
        'appliance_co2': json.dumps(appliance_co2),
        'forecast_dates': json.dumps(forecast_dates),
        'forecast_kwh': json.dumps(forecast_kwh),
        'total_consumption': analytics['total_monthly_kwh'],
        'total_cost': analytics['total_monthly_cost'],
        'efficiency': analytics['efficiency_index'],
        'co2_emissions_kg': analytics['total_co2_kg'],
        'estimated_savings': analytics['estimated_savings'],
        'peak_load_kwh': analytics['peak_load_kwh'],
        'recommendations': analytics['recommendations'],
        'anomalies': anomalies,
        'predictions': recent_predictions,
    }
    return render(request, 'dashboard.html', context)


@login_required(login_url='login')
def add_appliances_view(request):
    """Add or update appliances."""
    user_profile = UserProfile.objects.get(user=request.user)

    if request.method == 'POST':
        names = request.POST.getlist('name[]')
        brands = request.POST.getlist('brand[]')
        models_list = request.POST.getlist('model[]')
        usage_times = request.POST.getlist('usage_time[]')
        quantities = request.POST.getlist('quantity[]')
        days_used_per_weeks = request.POST.getlist('days_used_per_week[]')
        power_ratings = request.POST.getlist('power_rating[]')

        if not names:
            # Check for single form fields
            single_name = request.POST.get('name')
            if single_name:
                names = [single_name]
                brands = [request.POST.get('brand', '')]
                models_list = [request.POST.get('model', '')]
                usage_times = [request.POST.get('usage_time', '1')]
                quantities = [request.POST.get('quantity', '1')]
                days_used_per_weeks = [request.POST.get('days_used_per_week', '7')]
                power_ratings = [request.POST.get('power_rating', '100')]

        if not names:
            messages.error(request, "Please fill out appliance details.")
            return render(request, 'add_appliances.html')

        added_count = 0
        for i in range(len(names)):
            try:
                name_str = names[i].strip()
                brand_str = brands[i].strip() if i < len(brands) else ''
                model_str = models_list[i].strip() if i < len(models_list) else ''

                full_appliance_name = name_str
                if brand_str or model_str:
                    full_appliance_name += f" ({brand_str} {model_str})".strip()

                usage_time = float(usage_times[i]) if i < len(usage_times) else 1.0
                quantity = int(quantities[i]) if i < len(quantities) else 1
                days_used_per_week = int(days_used_per_weeks[i]) if i < len(days_used_per_weeks) else 7
                power_rating = float(power_ratings[i]) if i < len(power_ratings) else 100.0

                appliance, created = Appliance.objects.get_or_create(
                    user_profile=user_profile,
                    name=full_appliance_name,
                    defaults={
                        'power_rating': power_rating,
                        'quantity': quantity,
                        'days_used_per_week': days_used_per_week,
                        'usage_time': usage_time,
                    }
                )
                if not created:
                    appliance.quantity += quantity
                    appliance.power_rating = power_rating
                    appliance.usage_time = usage_time
                    appliance.days_used_per_week = days_used_per_week
                    appliance.save()

                added_count += 1
            except (ValueError, IndexError):
                continue

        if added_count > 0:
            messages.success(request, f"Successfully saved {added_count} appliance(s).")
            # Refresh AI predictions
            generate_predictions_and_reports_for_user(user_profile)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid appliance input values.")

    return render(request, 'add_appliances.html')


@login_required(login_url='login')
def remove_appliance_view(request, appliance_id):
    """Remove appliance endpoint."""
    if request.method == 'POST':
        appliance = get_object_or_404(Appliance, id=appliance_id)
        if appliance.user_profile.user == request.user:
            user_profile = appliance.user_profile
            appliance.delete()
            # Refresh predictions
            generate_predictions_and_reports_for_user(user_profile)
            messages.success(request, "Appliance removed.")
            return redirect('dashboard')
        return HttpResponseForbidden("Permission denied.")
    return HttpResponseForbidden("Method not allowed.")


@staff_member_required
def admin_dashboard_view(request):
    """Enterprise Admin Management Portal."""
    user_profiles = UserProfile.objects.prefetch_related('appliances').select_related('user').all()
    total_users = user_profiles.count()
    total_appliances = Appliance.objects.count()

    # Total system monthly load
    all_appliances = Appliance.objects.all()
    total_system_kwh = sum(a.monthly_kwh for a in all_appliances)
    total_system_cost = sum(a.monthly_cost for a in all_appliances)

    context = {
        'user_profiles': user_profiles,
        'total_users': total_users,
        'total_appliances': total_appliances,
        'total_system_kwh': round(total_system_kwh, 2),
        'total_system_cost': round(total_system_cost, 2),
    }
    return render(request, 'admin_dashboard.html', context)


@staff_member_required
def admin_remove_appliance_view(request, appliance_id):
    if request.method == 'POST':
        appliance = get_object_or_404(Appliance, id=appliance_id)
        user_profile = appliance.user_profile
        appliance.delete()
        generate_predictions_and_reports_for_user(user_profile)
        messages.success(request, "Appliance removed by admin.")
        return redirect('admin_dashboard')
    return HttpResponseForbidden("Invalid method.")


@staff_member_required
def admin_add_appliance_view(request):
    if request.method == 'POST':
        user_profile_id = request.POST.get('user_profile_id')
        name = request.POST.get('name')
        power_rating = request.POST.get('power_rating')
        quantity = request.POST.get('quantity')

        if not (user_profile_id and name and power_rating and quantity):
            messages.error(request, "All fields are required.")
            return redirect('admin_dashboard')

        try:
            user_profile = UserProfile.objects.get(id=user_profile_id)
            Appliance.objects.create(
                user_profile=user_profile,
                name=name,
                power_rating=float(power_rating),
                quantity=int(quantity)
            )
            generate_predictions_and_reports_for_user(user_profile)
            messages.success(request, f"Appliance added for {user_profile.full_name}.")
        except (UserProfile.DoesNotExist, ValueError):
            messages.error(request, "Invalid data.")

        return redirect('admin_dashboard')
    return HttpResponseForbidden("Invalid method.")


@staff_member_required
def admin_remove_user_view(request, user_profile_id):
    if request.method == 'POST':
        user_profile = get_object_or_404(UserProfile, id=user_profile_id)
        user = user_profile.user
        user.delete()
        messages.success(request, f"User {user_profile.full_name} and all data removed.")
        return redirect('admin_dashboard')
    return HttpResponseForbidden("Invalid method.")


@login_required(login_url='login')
def appliances_list_view(request):
    user_profile = UserProfile.objects.get(user=request.user)
    appliances = Appliance.objects.filter(user_profile=user_profile)
    return render(request, 'appliances_list.html', {'appliances': appliances})


@login_required(login_url='login')
def consumption_view(request, appliance_id):
    appliance = get_object_or_404(Appliance, id=appliance_id, user_profile__user=request.user)
    consumptions = EnergyConsumption.objects.filter(appliance=appliance).order_by('-date')
    return render(request, 'consumption.html', {'appliance': appliance, 'consumptions': consumptions})


@login_required(login_url='login')
def predictions_view(request):
    user_profile = UserProfile.objects.get(user=request.user)
    predictions = Prediction.objects.filter(user_profile=user_profile).order_by('-predicted_date')
    return render(request, 'predictions.html', {'predictions': predictions})


@login_required(login_url='login')
def reports_view(request):
    user_profile = UserProfile.objects.get(user=request.user)
    reports = Report.objects.filter(user_profile=user_profile).order_by('-report_date')
    return render(request, 'reports.html', {'reports': reports})


@login_required(login_url='login')
def generate_predictions_view(request):
    user_profile = UserProfile.objects.get(user=request.user)
    generate_predictions_and_reports_for_user(user_profile)
    messages.success(request, "AI Machine Learning model predictions recomputed successfully.")
    return redirect('dashboard')



def logout_view(request):
    logout(request)
    messages.info(request, "You have logged out.")
    return redirect('login')
