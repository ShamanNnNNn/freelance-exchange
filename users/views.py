from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import auth, messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from order.models import Order
from users.forms import ProfileForm, UserLoginForm, UserRegistrationForm

def login(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = auth.authenticate(username=username, password=password)
            if user:
                auth.login(request, user)
                messages.success(request, f"{username}, Вы вошли в аккаунт")
                return HttpResponseRedirect(reverse('main:index'))
    else:
        form = UserLoginForm()
    context = {
        'title': "Авторизация",
        'form': form
    }
    return render(request, 'users/login.html', context)

def registration(request):
    if request.method == 'POST':
        form = UserRegistrationForm(data=request.POST)
        if form.is_valid():
                form.save()
                user = form.instance
                auth.login(request, user)
                messages.success(request, f"{user.username}, Вы успешно зарегистрированы")
                return HttpResponseRedirect(reverse('main:index'))
    else:
        form = UserRegistrationForm()
    context = {
        'title': "Регистрация",
        'form': form
    }
    return render(request, 'users/registration.html', context)

@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(data=request.POST, instance=request.user, files=request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request,  "Обновление успешно")
            return HttpResponseRedirect(reverse('user:profile'))
    else:
        form = ProfileForm(instance=request.user)
        
    user_orders = Order.objects.filter(Q(customer=request.user) | Q(freelancer=request.user))
    #user_announcements = Announcement.objects.filter(freelancer=request.user)
    completed_orders = user_orders.filter(status='completed').count()
    in_progress_orders = user_orders.filter(status='in_progress').count()
    context = {
    'title': "Профиль",
    'form': form,
    'user_orders': user_orders,
    #'user_announcements': user_announcements,
    'completed_orders': completed_orders,
    'in_progress_orders': in_progress_orders,
    }   
    
    return render(request, 'users/profile.html', context)

#def users_cart(request):
    #return render(request, "users/users_cart.html")
    
    

@login_required
def logout(request):
    messages.success(request, f"{request.user.username}, Вы вышли из аккаунта")
    auth.logout(request)
    return redirect(reverse('main:index'))