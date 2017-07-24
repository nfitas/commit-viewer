from __future__ import unicode_literals

from django.db import models

# Create your models here.

class Repository(models.Model):
	url	= models.TextField(primary_key=True)

class Commit(models.Model):
	identifier	= models.TextField()
	repository  = models.ForeignKey('Repository', to_field='url', on_delete=models.CASCADE)
	author 		= models.TextField()
	date		= models.TextField()
	description	= models.TextField()
	parents		= models.TextField()

	def __str__(self):
		return str(self.description)
