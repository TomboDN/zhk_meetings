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

from app import settings
from zhk_meetings_app import views as zhk_views
from django.views.static import serve

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
    path('meeting_format/<int:meeting_id>/', zhk_views.meeting_format_request, name='meeting_format'),
    path('meeting_questions/<int:meeting_id>/', zhk_views.meeting_questions, name='meeting_questions'),
    path('meeting_requirement_initiator_reason/<int:meeting_id>/', zhk_views.meeting_requirement_initiator_reason,
         name='meeting_requirement_initiator_reason'),
    path('meeting_requirement_creation/<int:meeting_id>/', zhk_views.meeting_requirement_creation,
         name='meeting_requirement_creation'),
    path('meeting_requirement_approval/<int:meeting_id>/', zhk_views.meeting_requirement_approval,
         name='meeting_requirement_approval'),
    path('meeting_cooperative_reorganization/<int:meeting_id>/', zhk_views.meeting_cooperative_reorganization,
         name='meeting_cooperative_reorganization'),
    path('meeting_power_termination/<int:meeting_id>/', zhk_views.meeting_power_termination,
         name='meeting_power_termination'),
    path('meeting_members_reception/<int:meeting_id>/', zhk_views.meeting_members_reception,
         name='meeting_members_reception'),
    path('meeting_preparation/<int:meeting_id>/', zhk_views.meeting_preparation, name='meeting_preparation'),
    path('meeting_execution/<int:meeting_id>/', zhk_views.meeting_execution, name='meeting_execution'),
    path('meeting_execution_intramural/<int:meeting_id>/', zhk_views.meeting_execution_attendance_intramural, 
         name='meeting_execution_intramural'),
    path('meeting_execution_extramural/<int:meeting_id>/', zhk_views.meeting_execution_attendance_extramural, 
         name='meeting_execution_extramural'),
    path('execution_before_info/<int:meeting_id>/<int:question_id>/<int:sub_question_id>/',
         zhk_views.execution_before_info, name='execution_before_info'),
    path('execution_common_info/<int:meeting_id>/<int:question_id>/<int:sub_question_id>/',
         zhk_views.execution_common_info, name='execution_common_info'),
    path('execution_voting/<int:meeting_id>/<int:question_id>/<int:sub_question_id>/',
         zhk_views.execution_voting, name='execution_voting'),
    path('execution_after_info/<int:meeting_id>/<int:question_id>/<int:sub_question_id>/',
         zhk_views.execution_after_info, name='execution_after_info'),
    path('meeting_finish/<int:meeting_id>/', zhk_views.meeting_finish,
         name='meeting_finish'),
    path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]
