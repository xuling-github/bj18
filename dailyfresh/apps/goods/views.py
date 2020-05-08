from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from goods.models import GoodsType, GoodsSKU, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from django_redis import get_redis_connection
from django.core.cache import cache
from order.models import OrderGoods

# Create your views here.

class IndexView(View):
    """首页"""
    def get(self, request):
        """显示首页"""
        # 尝试从缓存中获取数据
        context = cache.get('index_page_data')
        if context is None:
            # 获取商品的种类信息
            types =GoodsType.objects.all()
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

            context = {'types': types,
                       'goods_banners': goods_banners,
                       'promotion_banners': promotion_banners}
            # 设置缓存
            #          key                value   过期时间
            cache.set('index_page_data', context, 3600)
        # 获取购物车中商品数量
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d'%user.id
            cart_count = conn.hlen(cart_key)

        # 组织上下文
        # 给缓存中的数据更新购物车内容
        context.update(cart_count=cart_count)
        # 使用模板
        return render(request, 'index.html', context)

# /goods/商品id
class DetailView(View):
    """详情页"""
    def get(self, request, goods_id):
        """显示详情页"""
        try:
            sku = GoodsSKU.objects.get(id=sku.id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在
            return redirect(reverse('goods:index'))

        # 获取商品的分类信息
        types = GoodsType.objects.all()
        # 获取商品的不包含空的评论信息
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')
        # 获取新品信息,种类要同商品分类信息种类相同，
        # 根据base_model.py的创建时间加负号降序排序,取前两个
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]
        # 获取同一个SPU其他规格的商品,               exclude本次点击的商品
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)
        # 获取购物车中商品数量
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

            # 添加用户的历史浏览记录
            conn = get_redis_connection('default')
            history_key = 'history_%d'% user.id
            # 移除列表的goods_id  key count=0表示移除所有 value
            conn.lrem(history_key, 0, goods_id)
            # 将最新浏览的id插入到列表的左侧
            conn.lpush(history_key, goods_id)
            # 只保存用户浏览的前5条
            conn.ltrim(history_key, 0, 4)


        # 组织模板上下文
        context = {'sku':sku, 'types':types,
                   'sku_orders':sku_orders,
                   'new_skus':new_skus,
                   'same_spu_skus':same_spu_skus,
                   'cart_count':cart_count}

        return render(request, 'detail.html', context)


# /list/type_id/page?sort=
class ListView(View):
    """列表页"""
    def get(self,request,type_id,page):
        """显示列表页"""
        # 根据用户的type_id匹配商品种类并捕获异常
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist as e:
            # 种类不存在，重定向到首页
            return redirect(reverse('goods:index'))
        # 获取商品种类
        types = GoodsType.objects.all()
        # 获取用户对应商品种类id的商品信息. 通过url获取排序方式信息
        sort = request.Get.get('sort')
        # 根据价格排序
        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        # 根据销量排序
        if sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        # 其他情况默认根据id降序排序
        else:
            sort == 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')
        # 获取分页信息 django内置方法paginator获取一个分页对象实例
        paginator = Paginator(skus, 1)
        # 匹配用户的page并捕获异常，page需要是一个整数且，当page大于总页数page都设置为1
        try:
            page = int(page)
        except Exception as e:
            page = 1
        if page > paginator.num_pages:
            page = 1
        # 获取每page的所有对象
        page_skus = paginator.page(page)
        # 页码控制
        # 获取总页码
        num_pages = paginator.num_pages
        # 1.总页数不超过5,显示所有
        if num_pages < 5:
            pages = range(1,num_pages+1)
        # 2.当前页是前3页，显示全部1-5页
        elif page <=3:
            pages = range(1,6)
        # 3.当前页是全部页数后3页，显示后5页
        elif num_pages - page <= 2:
            pages = range(num_pages-4, num_pages+1)
        # 4.其他情况显示当前页的前两页，当前页，当前页后两页
        else:
            pages = range(page-2, page+3)
        # 根据base_model.py的创建时间加负号降序排序,取前两个
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]
        # 获取购物车中商品数量
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)
        # 组织上下文
        context = {
            "type":type, "types":types,
            "page_skus":page_skus,
            "pages":pages,
            "new_skus":new_skus,
            "cart_count":cart_count,
            "sort":sort
        }
        # 使用模板
        return render(request, 'list.html', context)
