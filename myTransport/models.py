#coding=utf-8
from django.db import models
from django.contrib.auth.models import Group,Permission,User
import datetime
# Create your models here.
class bindWorkId(models.Model):
	user = models.OneToOneField(User)
	workId = models.IntegerField()
	
	class Meta:
		db_table = 'bindWorkId'

	def getUser(self):
		return {'username':self.user.username,'is_active':self.user.is_active}
class userToken(models.Model):
	token = models.CharField(max_length=30)
	createTime = models.DateTimeField()
	user = models.ForeignKey(User)
	class Meta:
		db_table = 'userToken'
	def getToken(self):
		return {'username':self.user.username,'token':self.token}

class action_log(models.Model):
	user = models.OneToOneField(User)
	remote_addr = models.CharField(max_length=255)
	action = models.IntegerField(choices=[(0,'upload'),(1,'download')],help_text='0表示上传，1表示下载')
	file = models.TextField(blank=True, null=True)
	file_size = models.CharField(max_length=255)
	ops_time = models.DateTimeField(auto_now=True)
	class Meta:
		db_table = 'action_log'	

	def show_table(self):
		return {
			'username':self.user.username,
			'remote_addr':self.remote_addr,
			'action':self.action,
			'file':self.file,
			'file_size':self.file_size,
			'ops_time':self.ops_time.strftime('%Y-%m-%d %H:%M:%S')
		}