"""
Authentication views for PostPro.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .forms import LoginForm, RegisterForm


def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        if request.user.is_super_admin:
            return redirect('admin_panel:dashboard')
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                login(request, user)
                
                # Check for specific role redirects
                if user.is_super_admin:
                    return redirect('admin_panel:dashboard')
                
                # Default behavior
                next_url = request.GET.get('next')
                if not next_url or next_url == '/dashboard/':
                    return redirect('dashboard:index')
                return redirect(next_url)
            else:
                messages.error(request, 'Email ou senha inválidos.')
    else:
        form = LoginForm()
    
    return render(request, 'auth/login.html', {'form': form})


def register_view(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Conta criada com sucesso!')
            return redirect('dashboard:index')
    else:
        form = RegisterForm()
    
    return render(request, 'auth/register.html', {'form': form})


@login_required
def logout_view(request):
    """User logout view."""
    logout(request)
    messages.info(request, 'Você saiu da sua conta.')
    return redirect('accounts:login')


def home_view(request):
    """Home page redirect."""
    if request.user.is_authenticated:
        if request.user.is_super_admin:
            return redirect('admin_panel:dashboard')
        return redirect('dashboard:index')
    return redirect('accounts:login')
