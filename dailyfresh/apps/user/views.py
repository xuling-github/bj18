from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.core.mail import send_mail
from django_redis import get_redis_connection
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.conf import settings
from user.models import User, Address
from goods.models import GoodsSKU
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate, login, logout
from utils.mixin import LoginRequiredMixin
import re

# Create your views here.

# /user/register
#def register(request):
#    """显示注册页面"""
#    if request.method == 'GET':
#        return render(request, 'register.html')
#    else:
#        # 进行注册处理
#        # 接收数据
#        username = request.POST.get('user_name')
#        password = request.POST.get('pwd')
#        email = request.POST.get('email')
#        allow = request.POST.get('allow')
#        # 校验数据
#        if not all([username,password,email]):
#            # 数据不完整
#            return render(request,'register.html', {'errmsg':'数据不完整'})
#        
#        # 校验邮箱
#        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',email):
#            return render(request, 'register.html',{'errmsg':'邮箱格式不正确'})
#        if allow!= 'on':
#            return render(request, 'register.html',{'errmsg':'请同意协议'})
#        # 校验用户名是否重复
#        try:
#            user = User.objects.get(username=username)
#        except User.DoesNotExist:
#            # 用户名不存在
#            user = None
#        if user:
#            # 用户名已存在
#            return render(request, 'register.html', {'errmsg':'用户名已存在'})
#        # 进行各流程处理，业务处理：用户注册
#        # 导入User模块并创建user实例
#       # user = User()
#       # user.username = username
#       # user.password = password
#       # user.email = email
#       # user.save()
#        user = User.objects.create_user(username,password,email)
#        user.is_active = 0
#        user.save()
#
#        # 返回应答
#        return redirect(reverse('goods:index'))


# 类视图的使用
class RegisterView(View):
    """注册类"""
    # get请求方式就用get函数
    def get(self, request):
        """显示注册页面"""
        return render(request, 'register.html')

    def post(self, request):
        """进行注册处理"""
        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        print(email,password)
        # 校验数据
        if not all([username,password,email]):
            # 数据不完整
            return render(request,'register.html', {'errmsg':'数据不完整'})

        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',email):
            return render(request, 'register.html',{'errmsg':'邮箱格式不正确'})
        if allow!= 'on':
            return render(request, 'register.html',{'errmsg':'请同意协议'})
        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None
        if user:
            # 用户名已存在
            return render(request, 'register.html', {'errmsg':'用户名已存在'})
        # 进行各流程处理，业务处理：用户注册
        # 导入User模块并创建user实例
           # user = User()
           # user.username = username
           # user.password = password
           # user.email = email
           # user.save()
        user = User.objects.create_user(username,password,email)
        user.is_active = 0
        user.save()
        # 发送激活邮件，包含激活链接：http：//127.0.0.1：8000/user/active
        # 发送链接中包含用户身份信息并加密

        # 加密用户身份信息并生成激活token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm':user.id}
        token = serializer.dumps(info)  # 是一个bytes数据 为了在邮件中显示utf8格式需要进行解码
        token = token.decode("utf-8")

        # # 发送邮件
        # subject = '天天生鲜欢迎您' # 邮件主题
        # message = '' # 这个设置为空，用html_message传递正文
        # # 这个参数可以解析html代码
        # html_message = '<h1>%s,欢迎您成为天天生鲜注册会员，请点击下列链接激活您的账户</h1><br /><a href="http:127.0.0.1:8000/user/active/%s">http:127.0.0.1:8000/user/active/%s</a>' %(username,token,token) # 邮件
        # sender = settings.EMAIL_FROM  # 发件人
        # receiver = [email]  # 收件邮箱列表
        # #         前四个是按顺序传的后面html_message是关键字参数
        # send_mail(subject, message, sender, receiver, html_message=html_message)

        # 使用celery异步发送邮件
        send_register_active_email.delay(email, username, token)

        # 返回应答
        return redirect(reverse('goods:index'))


class ActiveView(View):
    """用户激活"""
    def get(self, request, token):
        """进行用户激活"""
        # 进行解密,获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取激活用户的ID
            user_id = info['confirm']
            # 根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 返回应答，跳转到登录页面
            return redirect(reverse('user:login'))

        except SignatureExpired as e:
            # 激活链接已过期
            return HttpResponse('激活链接已过期')

# /user/login
class LoginView(View):
    """登录视图"""
    def get(self, request):
        """显示登录页面"""
        # 在下一次登录时判断是否记住了用户名就是cookie里面有没有值
        if 'username' in request.COOKIES:
            # 获取这个用户名并且使用模板把这个值传到前端
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        # 使用模板
        return render(request, 'login.html', {'username':username,'checked':checked})
    def post(self, request):
        """登录处理"""
        # 接受数据
        username = request.POST.get("username")
        password = request.POST.get("pwd")
        # 数据完整性校验
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg':'用户名或密码不完整'})

        # 业务处理：登录校验
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户存在
            if user.is_active:
                # 用户已激活
                # 记录用户的登录状态
                login(request, user)

                # 获取登录后要跳转的地址
                next_url = request.GET.get('next', reverse('goods:index'))
                # 跳转到首页，借助这个HttpResponseRedirect类里面的session来设置cookie
                response = redirect(next_url)
                # 判断是否记住用户名
                remember = request.POST.get("remember")
                if remember == "on":
                    # 记住用户名
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    # 不记住
                    response.delete_cookie("username")

                # 返回应答
                return response
                # # 跳转到首页
                # return redirect(reverse('goods:index'))
            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg':'用户未激活'})
        else:
            # 用户名或者密码错误
            return render(request,'login.html', {'errmsg':'用户名或密码不正确'})


        # 返回应答


class LogoutView(LoginRequiredMixin, View):
    """退出登录"""
    def get(self,request):
        """退出登录"""
        # 清除用户的session信息
        logout(request)

        # 跳转到首页
        return redirect(reverse('goods:index'))


# /user
class UserInfoView(LoginRequiredMixin, View):
    """用户中心-信息页"""
    def get(self, request):
        # page='user' 模板变量
        # 如果用户登录，他的session中request.user是一个user的实例
        # 如果未登录，他是一个AnnoymousUser的实例
        # 这连个实例都有is_authenticated()方法，如果登录返回true，否则false

        # 获取用户个人信息
        user = request.user
        address = Address.objects.get_default_address(user)

        # 获取用户的历史浏览记录
        # 拿到redis链接
        # from redis import StrictRedis
        # str = StrictRedis(host="127.0.0.1",port="6379",db=9)
        con = get_redis_connection("default")

        history_key = "history_%d"%user_id

        # 获取前五条浏览记录,带有商品id的列表
        sku_ids = con.lrange(history_key,0,4)

        # 从数据库 中查询用户浏览商品的具体信息
        # goods_li = GoodsSKU.objects.filter(id__in=sku_ids)
        # # 为了让商品信息按照客户浏览的信息排布，需要建立两层循环，
        # # 当我们的浏览的商品goods的id等于数据库中的sku_id时把它添加到这个商品信息列表中去
        # goods_res = []
        # for a_id in sku_ids:
        #     for goods in goods_li:
        #         a_id = goods.id
        #         goods_res.append(goods)

        # 遍历获取客户浏览的商品信息
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        # 组织上下文，让传递模板变量的代码看起来更加简洁
        context = {'page':'user',
                   'adderss':address,
                   'goods_li':goods_li}

        # 除了我们给模板文件传递的模板变量外，django还会把request.user也传给模板文件，
        # 所以可以直接在模板文件使用
        # return render(request, 'user_center_info.html', {'page':'user', 'adderss':address})
        return render(request, 'user_center_info.html', context)

# /user/order
class UserOrderView(LoginRequiredMixin, View):
    """用户中心-订单页"""
    def get(self, request):

        # 获取用户的订单信息

        return render(request, 'user_center_order.html', {'page':'order'})

# /user/address
class AddressView(LoginRequiredMixin, View):
    """用户中心-地址页"""
    def get(self, request):
        """显示"""
        # 获取登录用户的User对象
        user = request.user

        # 获取用户的默认收货地址
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 用户不存在默认地址
        #     address = None
        address = Address.objects.get_default_address(user)
        return render(request, 'user_center_site.html', {'page':'address', 'address':address})

    def post(self, reqeust):
        """地址的添加"""
        # 接收数据
        receiver = request.POST.get("receiver")
        addr = request.POST.get("addr")
        zip_code = request.POST.get("zip_code")
        phone = request.POST.get("phone")
        # 校验数据
        # 校验数据完整性
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg':'数据不完整'})
        # 手机格式校验
        if not re.match(r'^1[3|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '手机格式不正确'})
        # 业务处理：地址添加
        # 如果用户已存在默认地址，添加的收获地址不作为默认地址，否则作为默认地址
        # 获取登录用户的User对象
        user = request.user

        # 获取用户的默认收货地址
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 用户不存在默认地址
        #     address = None
        address = Address.objects.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default = True
        # 添加地址
        Address.objects.create(user=user,
                               receiver=receiver,
                                addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)
        # 返回应答,刷新地址页面
        return redirect(reverse('user:address'))

