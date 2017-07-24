from django.conf.urls import url, include
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^$', views.search_repo_view, name='search'),
    url(r'^project/$', views.fetch_repo_view, name='repo-fetch'),
  	#Fix urls to accept . / :
    url(r'^project/(?P<pk>.*)$', views.list_commits_view, name='list'),
]
