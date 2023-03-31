"""app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from zhk_meetings_app import views as zhk_views

urlpatterns = [
    path('', zhk_views.home, name='home'),
    path('dashboard/', zhk_views.dashboard, name='dashboard'),
    path('admin/', admin.site.urls),
    path('register/', zhk_views.register_request, name='register'),
    path('login/', zhk_views.login_request, name='login'),
    path('logout/', zhk_views.logout_request, name='logout'),
    path('main_data/', zhk_views.cooperative_main_data, name='main_data'),
    path('members_data/', zhk_views.cooperative_members_data, name='members_data'),
    path('meeting_new/', zhk_views.cooperative_meeting_new, name='meeting_new'),
    path('regular_questions/', zhk_views.regular_questions, name='regular_questions'),
    path('irregular_intramural_questions/', zhk_views.irregular_intramural_questions, name='irregular_intramural_questions'),
    path('irregular_extramural_questions/', zhk_views.irregular_extramural_questions, name='irregular_extramural_questions'),
]
