from django.conf import settings
from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client

class FDFSStorage(Storage):
    """fastdfs文件存储类"""

    def __init__(self, client_conf=None,base_url=None):
        if client_conf == None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

        if base_url == None:
            base_url = settings.FDFS_URL
        self.base_url = base_url


    def _open(self, name, mode='rb'):
        """打开文件时使用"""
        pass

    def _save(self, name, content):
        """保存文件时使用"""
        # name:你选择上传的文件的名字
        # content：包含你上传文件内容的file对象

        # 创建一个Fdfs_client对象
        client = Fdfs_client(self.client_conf)
        # 上传文件到fastdfs系统中
        res = client.upload_appender_by_buffer(content.read())
        print(res)
        # res是一个字典
        # dict
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,
        #     'Status': 'Upload successed.',
        #     'Local file name': '',
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # }
        if res.get('Status') != 'Upload successed.':
            # 上传失败

            raise Exception('上传文件到fastdfs失败')

        # 获取返回文件的id
        filename = res.get('Remote file_id')

        return filename
    def exists(self, name):
        """django 判断文件是否可用"""
        # 因为用的是其他服务器，所以文件名都是可用的，所以设置为不存在
        return False

    def url(self, name):
        """返回访问文件的url"""
        return self.base_url+name