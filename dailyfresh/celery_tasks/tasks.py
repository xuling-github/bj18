import os

from django.conf import settings
from django.template import loader, RequestContext
from django.core.mail import send_mail
from celery import Celery
import time
from goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from django_redis import get_redis_connection


# 在任务处理者中使用，这里不用
# import os
# import django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
# django.setup()


# 创建一个celery实例
#                路径                 中间人redis   redis-server进程中的ip和端口号
#                                     通过ps aux|grep redis-server查看
#                                                  /要使用的readis数据库号码
app = Celery('celery_tasks.tasks',broker='redis://127.0.0.1:6379/8')

# 定义任务函数
@app.task
def send_register_active_email(to_email,username, token):
    """发送激活邮件"""
    # 发送邮件
    subject = '天天生鲜欢迎您'  # 邮件主题
    message = ''  # 这个设置为空，用html_message传递正文
    # 这个参数可以解析html代码
    html_message = '<h1>%s,欢迎您成为天天生鲜注册会员，请点击下列链接激活您的账户</h1><br /><a href="http:127.0.0.1:8000/user/active/%s">http:127.0.0.1:8000/user/active/%s</a>' % (
    username, token, token)  # 邮件
    sender = settings.EMAIL_FROM  # 发件人
    receiver = [to_email]  # 收件邮箱列表
    #         前四个是按顺序传的后面html_message是关键字参数
    send_mail(subject, message, sender, receiver, html_message=html_message)
    time.sleep(5)

@app.task
def generate_static_index_html():
    # 获取商品的种类信息
    types = GoodsType.objects.all()
    # 获取首页轮播商品信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')
    # 获取促销活动信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
    # 获取首页商品展示信息
    # type_goods_banners = IndexTypeGoodsBanner.objects.all()
    for type in types:
        # 通过type种类匹配获取首页分类商品的图片展示信息以及文字信息   type种类匹配
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

    # 动态语言可以任意的给对象增加属性
    type.image_banners = image_banners
    type.title_banners = title_banners

    # 组织上下文
    context = {'types': types,
               'goods_banners': goods_banners,
               'promotion_banners': promotion_banners
               }
    # 使用模板
    # 1.加载模块
    temp = loader.get_template('static_index.html')
    # # 2.定义模板上下文
    # context = RequestContext(request, context)
    # 3.模板渲染
    static_index_html = temp.render(context)
    # 生成首页对应的静态文件
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')

    with open(save_path, 'w') as f:
        f.write(static_index_html)