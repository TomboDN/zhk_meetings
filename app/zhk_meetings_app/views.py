from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from .forms import UserRegisterForm, UserLoginForm, CooperativeDataForm
from .models import Cooperative


def register_request(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Создан аккаунт {username}!')
            return redirect('/login')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def login_request(request):
    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"Вы зашли как {username}.")
                return redirect('/')
            else:
                messages.error(request, "Неправильная почта или пароль.")
        else:
            messages.error(request, "Неправильная почта или пароль.")
    form = UserLoginForm()
    return render(request=request, template_name="registration/login.html", context={"form": form})


def logout_request(request):
    logout(request)
    messages.info(request, "Вы успешно вышли из аккаунта.")
    return redirect('/')


def home(request):
    return render(request=request, template_name="home.html")


def dashboard(request):
    return render(request=request, template_name="dashboard.html")


def cooperative_main_data(request):
    if request.method == "POST":
        form = CooperativeDataForm(request.POST)
        if form.is_valid():
            obj, created = Cooperative.objects.update_or_create(cooperative_user=request.user, defaults=dict(
                cooperative_type=form.cleaned_data.get('cooperative_type'),
                cooperative_name=form.cleaned_data.get('cooperative_name'),
                cooperative_itn=form.cleaned_data.get('cooperative_itn'),
                cooperative_address=form.cleaned_data.get('cooperative_address'),
                cooperative_email_address=form.cleaned_data.get('cooperative_email_address'),
                cooperative_telephone_number=form.cleaned_data.get('cooperative_telephone_number')))
            messages.info(request, f"Обновление {created}")
            return redirect('/')
        else:
            messages.error(request, "Ошибки в полях.")
    form = CooperativeDataForm()
    return render(request=request, template_name="cooperative_data/main_data.html", context={"form": form})
