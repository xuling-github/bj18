from django.shortcuts import render
from django.views.generic import View
from goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from django_redis import get_redis_connection

# Create your views here.

class IndexView(View):
    """首页"""
    def get(self, request):
        """显示首页"""
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
        # 获取购物车中商品数量
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d'%user.id
            cart_count = conn.hlen(cart_key)
        else:
            # 用户未登录，购物车数量显示0
            cart_count = 0
        # 组织上下文
        context = {'types':types,
                   'goods_banners':goods_banners,
                   'promotion_banners':promotion_banners,
                   #'type_goods_banners':type_goods_banners,
                   'cart_count':cart_count}
        # 使用模板
        return render(request, 'index.html', context)
