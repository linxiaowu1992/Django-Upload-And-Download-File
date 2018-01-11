# Django-Upload-And-Download-File
is a web tools for upload file from Intranet machine and downlown file to local machine
用于上传内网文件，并支持下载文件到本地

#start
init mysql:
 python manage.py makemigrations
 python manage.py migrate
running:
 python manage.py runserver
 
#basic setting:
setting in setting.py:
FILE_ROOT_DIR='/tmp/'      #directory to store files which uploaded
IP_WHITE_LIST = ['192.168','10.11']  #limit ips that allow upload files
UPLOAD_LIMIT = {
    'num':100, #max files every day of upload
    'size':100 #max size every day of upload (MB)
}
TAR_TEMP_DIR = '/tmp/filetransport_tar_temp'  #tar directory when downfile path is a directory,it will tar a tar.gz file in here 

#limit file type 
in file filetransport/myTransport/templates/upload.html:
example_dropzone = $("#advancedDropzone").dropzone({
			url: '/transport/upload/',
			maxFilesize:100,  //max size 100M
			maxFiles:100,     //max files 
			addRemoveLinks:true,
			acceptedFiles:'image/*,video/*',  //file types that allow upload
			dictInvalidFileType: "你不能上传该类型文件,文件类型只能是图片或视频。",
			dictFileTooBig:"文件过大上传文件最大支持.",
			dictFallbackMessage:"浏览器不受支持",
      ......
      
#note
you should create a user first
