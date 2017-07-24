import sys

from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist

from commits.models import Repository, Commit

from list_commit import list_commit

# Search View
def search_repo_view(request):

	repos = Repository.objects.all()

	context = {
			'repos' : repos,
			}
	
	return render(request, "commits/search_view.html", context)

# TODO Merge views (repo_fetch_view with list_commits_view) 
def fetch_repo_view(request):

	reponame = request.POST.get("reponame", None)

	context = {
			'reponame' : reponame,
			}

	# Retrieve commits if there is no commit list in DB
	try:
		Repository.objects.get(url=reponame)

	#TODO Fix catching this exception, it is not working when there is concurrency
	except Repository.DoesNotExist:

		# trying to retrieve commits remotely
		commit_retriever = list_commit.CommitRetriever(reponame)
		commits_list_response = commit_retriever.get_commits()
		print commits_list_response
		status = commits_list_response.get('Status','')
		if status != "OK":
			return HttpResponseRedirect(reverse('commits:search', args=(),kwargs={}))

		# storing retrieved commits for repository
		repo = Repository.objects.create(url=reponame)
		for commit in commits_list_response.get('commit_list'):
			p = Commit.objects.create(identifier=commit['sha'],
									repository=repo,
									author=commit['author_name'],
									date=commit['author_date'],
									description=commit['message'],
									parents=commit.get('parents',''),)

	return HttpResponseRedirect(reverse('commits:list', kwargs={'pk': reponame}))

#Lister view
def list_commits_view(request, pk=None):
	
	context = {
		'commits' : Commit.objects.filter(repository_id=pk),
		}

	context['reponame'] = pk
	return render (request, "commits/list_view.html", context)

	

