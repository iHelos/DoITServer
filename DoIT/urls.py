"""DoIT URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
# from django.contrib import admin
from rest_framework import routers
from DoITproject import views
from rest_framework.authtoken import views as restViews
from django.conf.urls import include, url

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
from DoITproject.views import device_register, confirm_registration

urlpatterns = [
    # url(r'^auth/$', restViews.obtain_auth_token),
    # url(r'^signup/$', views.sign_up),
    url(r'^task/create/$', views.task_create),
    url(r'^task/in/$', views.AllTasksInDetail.as_view()),
    url(r'^task/in/(?P<pk>[0-9]+)/$', views.TaskInDetail.as_view()),
    url(r'^task/out/$', views.AllTasksOutDetail.as_view()),
    url(r'^task/out/(?P<pk>[0-9]+)/$', views.TaskOutDetail.as_view()),
    url(r'^registerDevice/$', device_register),
    url(r'^confirm/$', confirm_registration),
    url(r'', include('gcm.urls')),
    url(r'^$', include('rest_framework_docs.urls')),
]
