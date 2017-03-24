# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
# from django.conf import settings

urlpatterns = patterns('www.admin.views',
                       url(r'^$', 'home'),
                       )

urlpatterns += patterns('www.admin.views_shop',
      url(r'^encouragement/get_encouragement_data$', 'get_encouragement_data'), 
      url(r'^encouragement$', 'encouragement'), 

      url(r'^order_list$', 'order_list'), 

      url(r'^choose_channel$', 'choose_channel'),  

      url(r'^timesharing/get_timesharing_detail_data$', 'get_timesharing_detail_data'),
      url(r'^timesharing/get_timesharing_statistics_data$', 'get_timesharing_statistics_data'),
      url(r'^timesharing$', 'timesharing'),

      url(r'^inactive_shops$', 'inactive_shops'),
      
      url(r'^salesman/get_salesman_statistics_data$', 'get_salesman_statistics_data'),
      url(r'^salesman$', 'salesman'),

      url(r'^shop/get_order_list$', 'get_order_list'),
      url(r'^shop/get_order_statistic_data$', 'get_order_statistic_data'),
      url(r'^shop/get_shop_sort$', 'get_shop_sort'),
      url(r'^per_shop/(?P<shop_id>\w+)/$', 'per_shop'),
      url(r'^shop$', 'shop'),
)

# 注册用户管理
urlpatterns += patterns('www.admin.views_user',

                        url(r'^user/change_pwd$', 'change_pwd'),
                        url(r'^user/add_user$', 'add_user'),
                        url(r'^user/get_user_by_nick$', 'get_user_by_nick'),
                        url(r'^user/modify_user$', 'modify_user'),
                        url(r'^user/get_user_by_id$', 'get_user_by_id'),
                        url(r'^user/search$', 'search'),
                        url(r'^user$', 'user'),
                        )

# 缓存管理
urlpatterns += patterns('www.admin.views_caches',

                        url(r'^caches/get_cache$', 'get_cache'),
                        url(r'^caches/remove_cache$', 'remove_cache'),
                        url(r'^caches/modify_cache$', 'modify_cache'),
                        url(r'^caches$', 'caches'),
                        )

# 权限
urlpatterns += patterns('www.admin.views_permission',

                        url(r'^permission/cancel_admin$', 'cancel_admin'),
                        url(r'^permission/save_user_permission$', 'save_user_permission'),
                        url(r'^permission/get_user_permissions$', 'get_user_permissions'),
                        url(r'^permission/get_all_administrators$', 'get_all_administrators'),
                        url(r'^permission$', 'permission'),
                        )
