
from django.db import models
from django.contrib.auth.models import AbstractUser
from db.base_model import BaseModel
# Create your models here.


class User(AbstractUser, BaseModel):
    '''用户模型类'''

    class Meta:
        db_table = 'df_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name


class AddressManager(models.Manager):
    """地址模型管理器类"""
    # 1.应用场景。1改变原有查询的结果：all()
    # 2.封装方法：用于操作模型类对应的数据表（增删改查）
    def get_default_address(self, user):
        """获取用户的默认地址"""
        # self.model：获取self对象所在的模型类
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 用户不存在默认地址
        #     address = None
        # try:
        #     address = self.model.objects.get(user=user, is_default=True)
        # except self.model.DoesNotExist:
        #     # 用户不存在默认地址
        #     address = None
        # self.model.objects.get改成self.get,因为他继承的父类modles.Manage可以直接使用get方法
        try:
            address = self.get(user=user, is_default=True)
        except self.model.DoesNotExist:
            # 用户不存在默认地址
            address = None

        return address
# 调用方法分析，Address调用地址模型类跳到我们自定义的objects方法，跳到调用地址模型管理器类，调用get_default_address方法
# 地址模型管理器类的调用方法 Address.objects.get_default_address(user)


class Address(BaseModel):
    '''地址模型类'''
    user = models.ForeignKey('User', verbose_name='所属账户')
    receiver = models.CharField(max_length=20, verbose_name='收件人')
    addr = models.CharField(max_length=256, verbose_name='收件地址')
    zip_code = models.CharField(max_length=6, null=True, verbose_name='邮政编码')
    phone = models.CharField(max_length=11, verbose_name='联系电话')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')

    # 自定义一个模型管理类对象
    objects = AddressManager()

    class Meta:
        db_table = 'df_address'
        verbose_name = '地址'
        verbose_name_plural = verbose_name
