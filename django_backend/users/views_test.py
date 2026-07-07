from django.shortcuts import render

def test_admin_dashboard(request):
    return render(request, 'admin_dashboard.html')
