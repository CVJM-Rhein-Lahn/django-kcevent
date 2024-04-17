"""konficastle URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.urls import path, include
from . import views
from . import admin as eventAdmin

urlpatterns = [
    path('partnership/', views.managePartnership, name='partnership'),
    path('events/', views.listEvents, name='listEvents'),
    path('login/<str:event_url>', views.registerEventLogin, name='registerEventLogin'),
    path('register/<str:event_url>', views.registerEvent, name='registerEvent'),
    path('dl/<str:event_url>', views.downloadRegistrationDocuments, name='downloadEventDocuments'),
    #path('admin/kcevent/<int:id>/participants', eventAdmin.event_part_view, name='part_view')
    path('', views.listPublicEvents, name='listPublicEvents'),

    #path('login/', views.user_login, name='user_login')
]
handler400 = views.responseError400
handler403 = views.responseError403
handler404 = views.responseError404
handler500 = views.responseError500
