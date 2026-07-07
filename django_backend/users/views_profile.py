from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from django.views.decorators.cache import never_cache

from django.contrib.auth import logout

@never_cache
@login_required(login_url='login')
def delete_account_view(request):
    if request.method == 'POST':
        user = request.user
        # Delete user and cascade delete related data
        user.delete()
        logout(request)  # Log out user after deletion to prevent access
        messages.success(request, "Your account has been deleted successfully.")
        return redirect('signup')
    elif request.method == 'GET':
        # Show confirmation page
        return render(request, 'delete_account_confirm.html')
    else:
        messages.error(request, "Invalid request method.")
        return redirect('dashboard')

@never_cache
@login_required(login_url='login')
def switch_account_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, "You have been logged out. Please log in with another account.")
        return redirect('login')
    elif request.method == 'GET':
        logout(request)
        messages.info(request, "You have been logged out. Please log in with another account.")
        return redirect('login')
    else:
        messages.error(request, "Invalid request method.")
        return redirect('dashboard')

@never_cache
@login_required(login_url='login')
def profile_view(request):
    from .models import UserProfile, Appliance
    user_profile = UserProfile.objects.get(user=request.user)
    appliances = Appliance.objects.filter(user_profile=user_profile)
    context = {
        'user_profile': user_profile,
        'appliances': appliances,
    }
    return render(request, 'profile.html', context)
