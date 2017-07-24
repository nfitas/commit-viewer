import subprocess, os
import tempfile
import shutil
import requests
import json
import abc

from secrets import git_user
from secrets import git_token


# Base Commit loader class
class CommitLoaderBase(object):
	__metaclass__ = abc.ABCMeta

	def __init__(self, repo_name):
		self.repo_name = repo_name
		self.commit_list = []

	@abc.abstractmethod
	def load(self):
		"""Retrieve commits of repository('repo_name', ex: codacy/commit-viewer) from the source.
		Returns a list, where each entry is a commit(map):
		# commit['sha']
		# commit['author_name']
		# commit['author_date']
		# commit['message'] 
		# commit['parents'] (if exists)
		"""
		return

# Commit loader using the Git CLI with Github repositories
# Creates a temporary clone of the repository to load the commit list
# TODO General to other git servers
class CommitLoaderGithubCLI(CommitLoaderBase):

	def load(self):

		# First, create a temporary folder and set the repo GitHub url
		repo_dtemp = tempfile.mkdtemp()
		repo_url = 'https://github.com/%s.git'%self.repo_name

		# Second, clone it in the temporary!
		try:
			self.git_clone(repo_dtemp, repo_url)
		except RuntimeError,e:
			#TODO Correctly identify when the repository does not exists
			shutil.rmtree(repo_dtemp)
			raise

		# Third, retrieve those commits.
		self.git_log(repo_dtemp)

		# Last, erase the temporary folder with the git clone
		shutil.rmtree(repo_dtemp)

		return self.commit_list


	# Clone repository to a given directory path using git CLI
	def git_clone(self, dirpath, repo_url):

		# TODO Correctly identify git folder ("which git")
		command =  "/usr/bin/git clone -n %s %s" % (repo_url, dirpath)

		pr = subprocess.Popen([command],                  
			   cwd=os.path.dirname(dirpath), 
			   stdout=subprocess.PIPE, 
			   stderr=subprocess.PIPE, 
			   shell=True)
		(out, error) = pr.communicate()

		if pr.returncode != 0:
			raise RuntimeError("%r failed, status code %s stderr %r" % (command, pr.returncode, error))


	# Retrieve commit list from a repository in a given directory parth using git CLI. Each commit is a map with:
	# commit['sha']
	# commit['author_name']
	# commit['author_date']
	# commit['message'] 
	# commit['parents'] (if exists)

	def git_log(self, dirpath):

		command = '/usr/bin/git log --pretty=format:"%H%x09%an%x09%ad%x09%s%x09%P"'

		pr = subprocess.Popen([command],                  
			   cwd=os.path.dirname(dirpath + "/"), 
			   stdout=subprocess.PIPE, 
			   stderr=subprocess.PIPE, 
			   shell=True)
		(out, error) = pr.communicate()

		if pr.returncode != 0:
			raise RuntimeError("%r failed, status code %s stderr %r" % (command, pr.returncode, error))

		for line in out.splitlines():

			line = line.strip().split('\t')

			commit = {}
			commit['sha'] = line[0]
			commit['author_name'] = line[1]
			commit['author_date'] = line[2]
			commit['message'] = line[3]
			if len(line) == 5:
				commit['parents'] = line[4]
			self.commit_list.append(commit)

		#return [s.strip().split('\t') for s in out.splitlines()]

# Commit loader using the Github API
# Loads commits list using GitHub REST API3.0 
class CommitLoaderGithubAPI(CommitLoaderBase):

	def load(self):

		# Set the REST API using pagination
		# TODO Use token credentials without commiting
		repo_url = 'https://%sapi.github.com/repos/%s/commits?page=1&per_page=100'%(git_user + git_token , self.repo_name)
		
		# Call Git Hub recursvly until there is no page left
		self.request_github_api(repo_url);
		
		return self.commit_list

	def request_github_api(self, repo_url):

		next_url = ""

		# First, call API
		try:
			response = requests.get(repo_url, timeout=3)
		except RuntimeError,e:
			raise

		# In case of status code NOK, abort
		if response.status_code != 200:
			# TODO Corretly identify when repo does not exist and properly deal with other error situations
			return

		commits = json.loads(response.text)

		# Second, map the commits of the atual page to a (cleaner) commit
		for commit_api in commits:

			commit = {}
			commit['sha'] = commit_api['sha']
			commit['author_name'] = commit_api['commit']['author']['name']
			commit['author_date'] = commit_api['commit']['author']['date']
			commit['message'] = commit_api['commit']['message']

			parent = ""
			for commit_parent in commit_api['parents']:
				parent = parent + ' ' + commit_parent['sha']
			if parent:
				commit['parents'] = parent
			self.commit_list.append(commit)

		# Third, find the next page url
		# TODO ?Increment page number until response is empty?
		try:
			for link in response.headers['Link'].split(','):
				if 'rel="next"' in link:
					next_url = link.split(';')[0].replace('<','').replace('>','')
		except KeyError:
			# If there is no 'Link' header, then this was the last page! (the end, my only friend)
			return

		if next_url:
			# Last, if there is a next URL. lets call the API again with next page url
			self.request_github_api(next_url);

		return

# Class with method (get_commits) to orchestrate different commits loaders
class CommitRetriever:

	def __init__(self, repo_name):
		self.repo_name = repo_name
		self.commit_list_response = {"Status" : "Empty"}

	def get_commits(self):
		try:
			print "Retrieving commits list by GitHub API."
			loader = CommitLoaderGithubAPI(self.repo_name)
			commit_list = loader.load()
		except Exception, e:
			print str(e)
			try:
				print "Oh no, API failed. Trying through CLI."
				loader = CommitLoaderGithubCLI(self.repo_name)
				commit_list = loader.load()
			except Exception, e:
				print str(e)
				return {"Status" : "NOK"}

		if commit_list:
			self.commit_list_response['Status'] = 'OK'
			self.commit_list_response['commit_list'] = commit_list
				
		return self.commit_list_response


if __name__ == '__main__':

	repo_name = 'diogo-aos/OOP'

	commits = CommitRetriever(repo_name)
	#print commits.get_commits()


