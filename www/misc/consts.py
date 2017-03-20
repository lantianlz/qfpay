# -*- coding: utf-8 -*-

'''
全局常量维护
'''

G_DICT_ERROR = {
    99600: u'不存在的用户',
    99601: u'找不到对象',
    99700: u'权限不足',
    99800: u'参数缺失',
    99801: u'参数异常',
    99802: u'参数重复',
    99900: u'系统错误',
    0: u'成功'
}


PERMISSIONS = [
    {'code': 'user_manage', 'name': u'用户管理', 'parent': None},
    {'code': 'add_user', 'name': u'添加用户', 'parent': 'user_manage'},
    {'code': 'query_user', 'name': u'查询用户', 'parent': 'user_manage'},
    {'code': 'modify_user', 'name': u'修改用户', 'parent': 'user_manage'},
    {'code': 'remove_user', 'name': u'删除用户', 'parent': 'user_manage'},
    {'code': 'change_pwd', 'name': u'修改用户密码', 'parent': 'user_manage'},

    {'code': 'news_manage', 'name': u'新闻管理', 'parent': None},
    {'code': 'add_news', 'name': u'添加新闻', 'parent': 'news_manage'},
    {'code': 'query_news', 'name': u'查询新闻', 'parent': 'news_manage'},
    {'code': 'modify_news', 'name': u'修改新闻', 'parent': 'news_manage'},

    {'code': 'activity_manage', 'name': u'活动管理', 'parent': None},
    {'code': 'add_activity', 'name': u'添加活动', 'parent': 'activity_manage'},
    {'code': 'query_activity', 'name': u'查询活动', 'parent': 'activity_manage'},
    {'code': 'modify_activity', 'name': u'修改活动', 'parent': 'activity_manage'},

    {'code': 'tools', 'name': u'常用工具', 'parent': None},
    {'code': 'get_cache', 'name': u'查询缓存', 'parent': 'tools'},
    {'code': 'remove_cache', 'name': u'删除缓存', 'parent': 'tools'},
    {'code': 'modify_cache', 'name': u'修改缓存', 'parent': 'tools'},

    {'code': 'permission_manage', 'name': u'权限管理', 'parent': None},
    {'code': 'add_user_permission', 'name': u'添加用户权限', 'parent': 'permission_manage'},
    {'code': 'query_user_permission', 'name': u'查询用户权限', 'parent': 'permission_manage'},
    {'code': 'modify_user_permission', 'name': u'修改用户权限', 'parent': 'permission_manage'},
    {'code': 'cancel_admin', 'name': u'取消管理员', 'parent': 'permission_manage'},
]
