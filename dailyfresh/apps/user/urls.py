from django.conf.urls import url
#from user import views
from django.contrib.auth.decorators import login_required

from user.views import RegisterView, ActiveView, LoginView, LogoutView, UserInfoView, UserOrderView, AddressView

urlpatterns = [
        #url(r'^register$', views.register, name='register'),  # 因为在配置文件的那个urls里面匹配了user/，这里就直接匹配register的开头和结尾
        #url(r'^register_handle$', views.register, name='register_handle'),  #注册处理
        url(r'^register$', RegisterView.as_view(), name='register'),  # 注册
        url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),  # 用户激活
        url(r'^login$', LoginView.as_view(), name='login'),  # 登录
        url(r'^logout$', LogoutView.as_view(), name='logout'),  #退出登录
        # url(r'^$', login_required(UserInfoView.as_view()), name='user'),  # 用户详情页
        # url(r'^order$', login_required(UserOrderView.as_view()), name='order'),  # 用户订单页
        # url(r'^address$', login_required(AddressView.as_view()), name='address'),  # 用户地址页
        url(r'^$', UserInfoView.as_view(), name='user'),  # 用户详情
        url(r'^order$', UserOrderView.as_view(), name='order'),  # 用户订单页
        url(r'^address$', AddressView.as_view(), name='address'),  # 用户地址页

]
