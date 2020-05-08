from django.conf.urls import url
from goods.views import IndexView, DetailView, ListView

urlpatterns = [
        url(r'^/index$', IndexView.as_view(), name='index'),  # 首页
        url(r'^goods/(?P<goods_id>\d+)$', DetailView.as_view(), name='detail'),  # 详情页，关键字参数就需要在视图函数中增加残念那你参数goods_id
        url(r'^list/(?P<type_id>)/(?P<page>)$', ListView.as_view(), name='list'),  # 列表页

]
