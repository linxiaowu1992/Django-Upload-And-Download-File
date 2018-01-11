#coding=utf-8
from django.shortcuts import render_to_response,render,RequestContext
from django.http import HttpResponse,HttpResponseRedirect,JsonResponse
from django.contrib.auth.models import *
from django.contrib.auth import authenticate,login
from django.db import transaction
from django.db.models import Prefetch,Q
import requests,random,string,datetime
from myTransport.models import *
import logging,os,sys,urllib,urllib2,json,time,traceback,datetime,re,tarfile
logger = logging.getLogger(__name__)
from django.conf import settings
from django.http import StreamingHttpResponse
import shutil
# Create your views here.
def mylogin(request):
	if request.method == 'GET':
		return render_to_response('login.html',{'error':request.session['errmsg'] if request.session.has_key('errmsg') else ''})
####主页
def index(request):
	return HttpResponseRedirect('/transport/page')
	#return render_to_response('index.html',{},context_instance=RequestContext(request))
def error403(request,msg):
	return render_to_response('error_403.html',{'msg':msg},context_instance=RequestContext(request))
###退出
def logout(request):
	del request.session['_auth_user_id']
	return HttpResponseRedirect('/login/')
####设置令牌token
def saveToken(loginUser,request=None):
	loginUserToken = ''.join(random.sample(string.ascii_letters + string.digits, 16))
	if request:
		request.session['Token'] = loginUserToken
	if loginUser.usertoken_set.all():
		loginUser.usertoken_set.all().update(
			token = loginUserToken,
			createTime = datetime.datetime.now()
		)

	else:
		userToken.objects.create(
			user = loginUser,
			token = loginUserToken,
			createTime = datetime.datetime.now()
		)

def upload_file(request,r_url):
	try:
		if request.method == 'POST':
			requestData = request.POST
		else:
			requestData = request.GET
		if r_url == 'page':
			return render_to_response('upload.html',{},context_instance=RequestContext(request))
		elif r_url == 'upload':
			#检查用户
			try:
				qs = User.objects.get(username=request.user)
			except Exception as e:
				logger.error("非法用户！")
				return JsonResponse({'code':403,'msg':'非法用户'})			
			logger.info("客户端ip:%s" % str(request.META.get("REMOTE_ADDR")))
			logger.info(request.META.get("HTTP_RELATIVE_PATH"))
			#检查客户端Ip是否为内部ip
			remote_addr = request.META.get("REMOTE_ADDR")
			isWhiteIp = False
			for item in settings.IP_WHITE_LIST:
				if remote_addr.startswith(item):
					isWhiteIp = True
					break
			if not isWhiteIp:
				logger.error("非法Ip:%s" % remote_addr)
				return JsonResponse({'code':403,'msg':"非法Ip:%s" % str(request.META.get("REMOTE_ADDR"))})
			upload_num,upload_sum = getUploadNumAndSize(request.user)
			if upload_num > settings.UPLOAD_LIMIT['num'] or upload_sum > settings.UPLOAD_LIMIT['size']:
				logger.error("用户的上传数额已达最大限制！")
				return JsonResponse({'code':403,'msg':"用户的上传数额已达最大限制！"})
			logger.info("用户 %s 上传文件%s..." % (str(request.user),str(request.FILES.get('file'))))
			requestData['relative_path'] = request.META.get("HTTP_RELATIVE_PATH")
			request_path = os.path.join(settings.FILE_ROOT_DIR,str(request.user))
			#检查用户空间
			if not os.path.exists(request_path):
				os.makedirs(request_path)
			if requestData.has_key('relative_path') and requestData['relative_path']:
				request_path = os.path.join(request_path,requestData['relative_path'])
			full_path = os.path.join(request_path,str(request.FILES.get('file')))
			#检查上传目录
			if not os.path.exists(request_path):
				logger.error('目录%s不存在!' % request_path.encode('utf-8','ignore'))
				return JsonResponse({'code':500,'msg':'目录或文件不存在'})	
			#写文件
			with open(full_path,'wb+') as f:
				for chunk in request.FILES.get('file').chunks():
					f.write(chunk)
			#获取文件大小并保持到日志
			fsize = os.path.getsize(full_path)/1024
			if int(fsize) < 1024:
				fsize = "{size}KB".format(size=str(fsize))
			else:
				fsize = "{size}MB".format(size=round(fsize/1024,2))
			action_log.objects.create(user=User.objects.get(username=request.user),
										action=0,
										remote_addr=remote_addr,
										file=full_path,
										file_size=fsize,
										ops_time=datetime.datetime.now())

			logger.info("用户 %s 上传文件%s成功！" % (str(request.user),str(request.FILES.get('file'))))
			return JsonResponse({'code':200})
		elif r_url == 'file_list':
			request_path = os.path.join(settings.FILE_ROOT_DIR,str(request.user))
			if requestData.has_key('relative_path') and requestData['relative_path']:
				request_path = os.path.join(request_path,requestData['relative_path'])
			logger.info("用户%s获取文件路径：%s" % (str(request.user),request_path.encode('utf-8','ignore')))
			if not os.path.exists(request_path):
				return JsonResponse({'code':500,'msg':'目录或文件不存在'})	
			file_list = {
				'relative_path':requestData['relative_path'],
				'dirs':[],
				'files':[],
			}
			for item in os.listdir(request_path):
				full_path = os.path.join(request_path,item)
				fsize = os.path.getsize(full_path)
				fmtime = timeStampToTime(os.path.getmtime(full_path))
				if os.path.isdir(full_path):
					file_list['dirs'].append({'name':item,'fsize':str(fsize)+'KB','fmtime':fmtime})
				else:
					file_list['files'].append({'name':item,'fsize':fsize,'fmtime':fmtime})
			
			return JsonResponse({'code':200,'data':file_list})					
	except Exception as e:
		logger.exception("Exception Logged")
		logger.error('发生异常:%s' % str(e))
		return JsonResponse({'code':500})
def download_file(request,r_url):
	try:
		if request.method == 'GET':
			requestData = request.GET
			try:
				qs = User.objects.get(username=request.user)
			except Exception as e:
				logger.error("非法用户！")
				return JsonResponse({'code':403,'msg':'非法用户'})
			if r_url == 'downloadFile' and requestData.has_key('relative_path') and requestData.has_key('filename'):
				request_path = os.path.join(settings.FILE_ROOT_DIR,str(request.user))
				if requestData['relative_path'] and requestData['filename']:
					request_path = os.path.join(request_path,requestData['relative_path'])
				full_path = os.path.join(request_path,requestData['filename'])
				remote_addr = request.META.get("REMOTE_ADDR")
				logger.info('用户%s下载文件%s...' % (str(request.user),full_path.encode('utf-8','ignore')))
				if not os.path.exists(full_path):
					logger.error('文件路径%s不存在！' % full_path.encode('utf-8','ignore'))
					return JsonResponse({'code':500})
				download_path = full_path
				if os.path.isdir(download_path):
					logger.info('路径为目录，开始打包压缩目录%s...' % download_path.encode('utf-8','ignore'))
					if not os.path.exists(settings.TAR_TEMP_DIR):
						os.makedirs(settings.TAR_TEMP_DIR)
					logger.info(os.path.basename(download_path))
					with tarfile.open(os.path.join(settings.TAR_TEMP_DIR,os.path.basename(download_path))+".tar.gz","w:gz") as tar:
							tar.add(download_path, arcname=os.path.basename(download_path))					
					download_path = os.path.join(settings.TAR_TEMP_DIR,tar.name)
					logger.info("tar name:" + tar.name)
					logger.info(download_path)
				#获取文件大小并保持到日志
				fsize = os.path.getsize(download_path)/1024
				if int(fsize) < 1024:
					fsize = "{size}KB".format(size=str(fsize))
				else:
					fsize = "{size}MB".format(size=round(fsize/1024,2))				
							
				response = big_file_download(request, download_path)
				action_log.objects.create(user=User.objects.get(username=request.user),
										action=1,
										remote_addr=remote_addr,
										file=full_path,
										file_size=fsize,
										ops_time=datetime.datetime.now())	
				#if download_path.startswith(settings.TAR_TEMP_DIR) and download_path.endswith('tar.gz'):
				#	os.remove(download_path)				
				logger.info("返回下载文件数据...")
				return response
				#return JsonResponse({'code':200})
			else:
				logger.error('下载参数不完整：%s' % str(requestData))
				return JsonResponse({'code':500,'msg':'下载参数不完整!'})
		#else:
		#	requestData = request.GET
		#	if requestData.has_key('type'):
		#		if requestData['type'] == 'page':
		#			return render_to_response('download.html',{},context_instance=RequestContext(request))
	except Exception as e:
		logger.exception("Exception Logged")
		logger.error('发生异常:%s' % str(e))
		return JsonResponse({'code':500})

def createDir(request):
	try:
		if request.method == 'POST':
			requestData = request.POST
			if requestData['dirName']:
				request_path = os.path.join(settings.FILE_ROOT_DIR,str(request.user))
				if not os.path.exists(request_path):
					os.makedirs(request_path)
				if requestData.has_key('relative_path') and requestData['relative_path']:
					request_path = os.path.join(request_path,requestData['relative_path'])
				#检查目录
				if not os.path.exists(request_path):
					logger.error('目录%s不存在!' % request_path.encode('utf-8','ignore'))
					return JsonResponse({'code':500,'msg':'目录或文件不存在'})	
				#创建目录
				request_path = os.path.join(request_path,requestData['dirName'])
				if os.path.isdir(request_path):
					logger.error('目录%s已存在，创建失败!' % request_path.encode('utf-8','ignore'))	
					return JsonResponse({'code':500,'msg':'目录已存在'})	
				else:
					os.makedirs(request_path)
					return JsonResponse({'code':200})

	except Exception as e:
		logger.exception("exception log")
		logger.error(str(e))
		return JsonResponse({'code':500,'msg':'创建目录失败！'})
def removeFile(request):
	try:
		if request.method == 'POST':
			requestData = request.POST
			if requestData['filename']:
				request_path = os.path.join(settings.FILE_ROOT_DIR,str(request.user))
				if requestData.has_key('relative_path') and requestData['relative_path']:
					request_path = os.path.join(request_path,requestData['relative_path'])
				request_path = os.path.join(request_path,requestData['filename'])
				logger.info("用户%s 删除文件%s" % (request.user,request_path.encode('utf-8','ignore')))
				if not os.path.exists(request_path):
					logger.error('目录%s不存在!' % request_path.encode('utf-8','ignore'))
					return JsonResponse({'code':500,'msg':'目录或文件不存在'})	
				if os.path.isdir(request_path):
					shutil.rmtree(request_path) 
				else:
					os.remove(request_path)
				return JsonResponse({'code':200})
	except Exception as e:
		logger.exception("exception log")
		logger.error(str(e))
		return JsonResponse({'code':500,'msg':'删除失败！'})
def logOption(request,r_url):
	try:
		if request.method == 'GET':
			requestData = request.GET
			if r_url == 'page':
				return render_to_response('log.html',{},context_instance=RequestContext(request))
			elif r_url == 'getLogData':
				logger.info('获取日志数据...')
				resultData = {
					'recordsTotal':0,
					'recordsFiltered':0,
					'data':[]
				}
				length = int(request.GET.get('length'))
				start = int(request.GET.get('start'))
				search = (request.GET.get('search[value]'))
				orderable = {
					'0':'user',
					'1':'remote_addr',
					'2':'action',
					'3':'file',
					'4':'file_size',
					'5':'ops_time'
				}
				###排序
				order = orderable[str(request.GET.get('order[0][column]'))]
				if request.GET.get('order[0][dir]')== 'desc':
					order = '-'+order
				###模糊搜索
				qs = Q()
				for index in range(1,6):
					qs = qs | Q(**{orderable[str(index)]+"__icontains":search})
				if search:
					resultData['data'] = [item.show_table() for item in action_log.objects.filter(qs).order_by(order)[start:start+length]]
					resultData['recordsTotal'] = action_log.objects.filter(qs).count()
					resultData['recordsFiltered'] = len(resultData['data'])
				else:
					resultData['data'] = [item.show_table() for item in action_log.objects.all().order_by(order)[start:start+length]]
					resultData['recordsTotal'] = action_log.objects.all().count()
					resultData['recordsFiltered'] = resultData['recordsTotal']		
				return JsonResponse(resultData)

	except Exception as e:
		logger.exception("Exception Logged")
		logger.error("发生异常：%s" % str(e))

####用户管理
def userOption(request,r_url):
	try:
		####新增
		if r_url=='add':
			with transaction.atomic():
				if request.POST.get('username','') == '' or request.POST.get('email','')=='' or request.POST.get('name','')=='':
					return JsonResponse({'code':False,'msg':'信息不全！'})
				if not request.POST.get('passWord','') == '' and request.POST.get('passWord','') == request.POST.get('confrimPW',''):
					if User.objects.filter(username=request.POST.get('username')):
						return JsonResponse({'code':False,'msg':'用户名已存在！'})
					user = User.objects.create_user(request.POST.get('username'), request.POST.get('email'), request.POST.get('passWord'))
					user.first_name = request.POST.get('name')
					user.is_superuser = int(request.POST.get('is_superuser'))
					if request.POST.get('workId',''):
						bindWorkId.objects.create(user = user,workId = request.POST.get('workId',''))
					else:
						return JsonResponse({'code':False,'msg':'工号不能为空！'})
					user.save()
					return JsonResponse({'code':True})
				else:
					return JsonResponse({'code':False,'msg':'密码校验不正确'})
		elif r_url=='update':
			type = request.POST.get('type')
			####单个用户激活注销
			with transaction.atomic():
				if type == 'isActive':
					user = User.objects.get(id=request.POST.get('id'))
					if request.POST.get('switch')=='active':
						user.is_active = 1
					else:
						user.is_active = 0
					user.save()
					return JsonResponse({'code':True })
				####单个用户更新信息
				elif type == 'updateMsg':
					user = User.objects.get(username=request.POST.get('username'))
					user.email = request.POST.get('email')
					user.first_name = request.POST.get('name')
					user.is_superuser = int(request.POST.get('is_superuser'))
					if not request.POST.get('passWord','') == '' and request.POST.get('passWord','') == request.POST.get('confrimPW',''):
						user.set_password(request.POST.get('passWord',''))

					if not request.POST.get('workId','') == '':
						bind = bindWorkId.objects.filter(user = user)
						if bind:
							bind[0].workId = request.POST.get('workId')
							bind[0].save()
						else:
							bindWorkId.objects.create(user = user,workId = request.POST.get('workId'))

					user.save()


					return JsonResponse({'code':True})
				####批量激活、注销
				elif  type == 'batchIsActive':
					if request.POST.get('isActive')=='active':
						User.objects.filter(id__in = json.loads(request.POST.get('idList'))).update(is_active=1)
					elif request.POST.get('isActive')=='cannel':
						User.objects.filter(id__in = json.loads(request.POST.get('idList'))).update(is_active=0)
					else:
						return JsonResponse({'code':False,'msg':'参数错误！'})
					return JsonResponse({'code':True})
		elif r_url == 'del':
			####删除单个用户
			type = request.POST.get('type')
			with transaction.atomic():
				if type == 'single':
					User.objects.get(id=request.POST.get('id')).delete()
				elif type == 'batch':
					User.objects.filter(id__in = json.loads(request.POST.get('idList'))).delete()
				else:
					return JsonResponse({'code':False,'msg':'参数错误！'})
				return JsonResponse({'code':True})
		elif r_url == 'get':
			if request.method == 'GET':
				if request.GET.has_key('type'):
					type = request.GET.get('type')
					if type == 'getData':
						userDict = {
							'recordsTotal':0,
							'recordsFiltered':0,
							'data':[]
						}
						length = int(request.GET.get('length'))
						start = int(request.GET.get('start'))
						search = (request.GET.get('search[value]'))
						orderable = {
							'1':'username',
							'2':'first_name',
							'3':'email',
							'4':'date_joined',
							'5':'is_active',
						}
						###排序
						order = orderable[str(request.GET.get('order[0][column]'))]
						if request.GET.get('order[0][dir]')== 'desc':
							order = '-'+order
						###模糊搜索
						qs = Q()
						for index in range(1,6):
							qs = qs | Q(**{orderable[str(index)]+"__icontains":search})
						if search:
							for u in User.objects.filter(qs).order_by(order)[start:start+length]:
								bind = bindWorkId.objects.filter(user = u)
								logger.info('is_superuser:'+str(u.is_superuser))
								userDict['data'].append({
									'id':u.id,
									'is_superuser':u.is_superuser,
									'username':u.username,
									'email':u.email,
									'name':u.first_name,
									'last_login':u.date_joined.strftime("%Y-%m-%d %H:%M:%S"),
									'workId':bind[0].workId if bind else '',
									'isActive': True if u.is_active==1 else False,
								})
								userDict['recordsTotal'] = User.objects.all().count()
								userDict['recordsFiltered'] = len(userDict['data'])
						else:
							for u in User.objects.all().order_by(order)[start:start+length]:
								bind = bindWorkId.objects.filter(user = u)
								logger.info('is_superuser:'+str(u.is_superuser))
								userDict['data'].append(
									{
										'id':u.id,
										'is_superuser':u.is_superuser,
										'username':u.username,
										'email':u.email,
										'name':u.first_name,
										'last_login':u.date_joined.strftime("%Y-%m-%d %H:%M:%S"),
										'workId':bind[0].workId if bind else '',
										'isActive': True if u.is_active==1 else False,
									}
								)
							userDict['recordsTotal'] = User.objects.all().count()
							userDict['recordsFiltered'] = User.objects.all().count()
						return JsonResponse(userDict)
				else:
					#####用户管理页面
					return  render_to_response('userManage.html',{},context_instance=RequestContext(request))
		elif r_url == 'page':
			return  render_to_response('userManage.html',{},context_instance=RequestContext(request))
		else:
			return render_to_response('error_500.html',{'msg':'请求地址出错！'},context_instance=RequestContext(request))

	except Exception,e:
		logger.exception("exception log")
		logger.error(str(e))
		return JsonResponse({'code':False,'msg':str(e)})

def postRes(url,data={},header={'Accept': 'application/json'}):
	postData = urllib.urlencode(data)
	req = urllib2.Request(url, postData, header)
	f = urllib2.urlopen(req)
	rdict = json.loads(f.read())
	return rdict

def getFileListFromClient(username,relative_path):
	url = settings.CLIENT_OPTION_URL
	data = {
		'type':'getFileList',
		'username': username,
		'relative_path':relative_path
	}
	return postRes(url,data)
def timeStampToTime(timestamp):
	timeStruct = time.localtime(timestamp)
	return time.strftime('%Y-%m-%d %H:%M:%S',timeStruct)



def big_file_download(request,download_path):

  def file_iterator(file_name, chunk_size=512):
    with open(file_name) as f:
      while True:
        c = f.read(chunk_size)
        if c:
          yield c
        else:
          break
  logger.info(os.path.basename(download_path))
  response = StreamingHttpResponse(file_iterator(download_path))
  response['Content-Type'] = 'application/octet-stream'
  response['Content-Length'] = os.path.getsize(download_path)
  response['Content-Disposition'] = 'attachment;filename="{0}"'.format(os.path.basename(download_path).encode('utf-8','ignore'))

  return response

def getUploadNumAndSize(username):
	qs = action_log.objects.filter(user=User.objects.get(username=username),action=0,ops_time__gt=datetime.date.today())
	upload_num = qs.count()
	item_list = [float(item.file_size.split('KB')[0]) if item.file_size.endswith('KB') else float(item.file_size.split('MB')[0])*1024 for item in qs]
	upload_sum = sum(item_list)/1024
	return upload_num,upload_sum
	

