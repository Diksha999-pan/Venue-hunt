from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, ProfileUpdateForm

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                next_url = request.GET.get('next', 'home')
                if user.user_type == 'vendor':
                    return redirect('venues:vendor_dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, 'Account created successfully!')
                if user.user_type == 'vendor':
                    return redirect('venues:vendor_dashboard')
                return redirect('home')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    context = {
        'form': form,
        'user': request.user
    }
    return render(request, 'accounts/profile.html', context)
