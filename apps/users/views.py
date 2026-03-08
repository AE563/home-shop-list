from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


def login_view(request):
    """FR-01: Login with email + password. Redirect to / on success."""
    if request.user.is_authenticated:
        return redirect('/')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        error = 'Неверный email или пароль.'

    return render(request, 'users/login.html', {'error': error})


@login_required
def logout_view(request):
    """FR-02: Logout and redirect to /login/."""
    logout(request)
    return redirect('/login/')