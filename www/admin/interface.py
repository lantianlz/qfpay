# -*- coding: utf-8 -*-
import datetime
from django.db.models import Count, Sum
from django.db import transaction

from common import debug, cache, raw_sql
from www.misc import consts
from www.misc.decorators import cache_required

from www.admin.models import Permission, UserPermission, Shop, Order, UserToChannel
from www.account.interface import UserBase


dict_err = {
    20101: u'已经存在相同名称的活动',
    20201: u'已经存在相同名称的新闻',
    20202: u'没有找到对应的新闻',
}

dict_err.update(consts.G_DICT_ERROR)

class PermissionBase(object):

    """docstring for PermissionBase"""

    def __init__(self):
        pass

    def get_all_permissions(self):
        '''
        获取所有权限
        '''
        return [x for x in Permission.objects.filter(parent__isnull=True)]

    def get_user_permissions(self, user_id):
        '''
        根据用户id 获取此用户所有权限
        '''
        return [x.permission.code for x in UserPermission.objects.select_related('permission').filter(user_id=user_id)]

    def get_all_administrators(self):
        '''
        获取所有管理员
        '''
        user_ids = [x['user_id'] for x in UserPermission.objects.values('user_id').annotate(dcount=Count('user_id'))]

        return [UserBase().get_user_by_id(x) for x in user_ids]

    @transaction.commit_manually
    def save_user_permission(self, user_id, permissions, creator):
        '''
        修改用户权限
        '''

        if not user_id or not permissions or not creator:
            return 99800, dict_err.get(99800)

        try:
            UserPermission.objects.filter(user_id=user_id).delete()

            for x in permissions:
                UserPermission.objects.create(user_id=user_id, permission_id=x, creator=creator)

            transaction.commit()
        except Exception, e:
            print e
            transaction.rollback()
            return 99900, dict_err.get(99900)

        return 0, dict_err.get(0)

    def cancel_admin(self, user_id):
        '''
        取消管理员
        '''

        if not user_id:
            return 99800, dict_err.get(99800)

        UserPermission.objects.filter(user_id=user_id).delete()

        return 0, dict_err.get(0)


class ShopBase(object):

    def __init__(self, channel_id):
        self.channel_id = channel_id

    def get_shop_by_id(self, shop_id):
        try:
            ps = dict(shop_id=shop_id)

            return Shop.objects.get(**ps)
        except Shop.DoesNotExist:
            return ""

    def get_shop_sort(self, start_date, end_date, pass_date_sort=False, salesman=None):
        '''
        获取店铺排行
        '''
        condition = " AND a.channel_id = %s " % self.channel_id

        if salesman:
            condition += " AND a.owner = '%s' " % salesman

        sort_str = 'total'
        if pass_date_sort:
            sort_str = 'pass_date'

        sql = """
            SELECT a.shop_id, a.name, COUNT(a.shop_id), SUM(b.price) AS total, pass_date
            FROM admin_shop a, admin_order b 
            WHERE %s <= b.order_date AND b.order_date <= %s
            AND a.shop_id = b.shop_id
        """ + condition + """
            GROUP BY a.shop_id
            ORDER BY 
        """ + sort_str + """ DESC
        """

        return raw_sql.exec_sql(sql, [start_date, end_date])

    def get_order_count(self, start_date, end_date, over_ten=False, shop_id=None, salesman=None):
        '''
        按日期 获取商户交易笔数分组
        '''
        condition = " AND b.channel_id = %s " % self.channel_id

        if over_ten:
            condition += " AND b.price >= 10 "
        if shop_id:
            condition += " AND b.shop_id = %s " % shop_id
        if salesman:
            condition += " AND a.owner = '%s' " % salesman

        sql = """
            SELECT DATE_FORMAT(b.order_date, "%%Y-%%m-%%d"), COUNT(b.shop_id)
            FROM admin_shop a, admin_order b
            WHERE %s <= b.order_date AND b.order_date <= %s
            AND a.shop_id = b.shop_id
        """ + condition + """
            GROUP BY DATE_FORMAT(b.order_date, "%%Y-%%m-%%d")
        """

        return raw_sql.exec_sql(sql, [start_date, end_date])

    def get_order_price(self, start_date, end_date, over_ten=False, shop_id=None, salesman=None):
        '''
        按日期 获取商户交易金额分组
        '''

        condition = " AND b.channel_id = %s " % self.channel_id

        if over_ten:
            condition += " AND b.price >= 10 "
        if shop_id:
            condition += " AND b.shop_id = %s " % shop_id
        if salesman:
            condition += " AND a.owner = '%s' " % salesman

        sql = """
            SELECT DATE_FORMAT(b.order_date, "%%Y-%%m-%%d"), SUM(b.price)
            FROM admin_shop a, admin_order b
            WHERE %s <= b.order_date AND b.order_date <= %s
            AND a.shop_id = b.shop_id
        """ + condition + """
            GROUP BY DATE_FORMAT(b.order_date, "%%Y-%%m-%%d")
        """

        return raw_sql.exec_sql(sql, [start_date, end_date])

    def get_order_list(self, start_date, end_date, price_sort, shop_id, salesman=None):
        '''
        获取商户交易流水
        '''
        
        condition = " AND b.channel_id = %s " % self.channel_id

        if shop_id:
            condition += " AND b.shop_id = %s " % shop_id
        if salesman:
            condition += " AND a.owner = '%s' " % salesman
        if price_sort:
            condition += " order by price desc"
        else:
            condition += " order by order_date desc"

        sql = """
            SELECT a.name, b.order_no, b.card_no, b.order_date, b.price, b.type, b.state
            FROM admin_shop a, admin_order b
            WHERE %s <= b.order_date AND b.order_date <= %s
            AND a.shop_id = b.shop_id
        """ + condition

        return raw_sql.exec_sql(sql, [start_date, end_date])

    def get_order_total_group_by_shop(self, start_date, end_date, over_ten=False):
        '''
        按店铺id 获取商户交易额分组
        '''
        objs = Order.objects.filter(
            channel_id=self.channel_id, 
            order_date__range=(start_date, end_date)
        )
        if over_ten:
            objs = objs.filter(price__gte=10)

        return objs.values('shop_id').annotate(Sum('price'))

    def get_order_total_and_rate_group_by_shop(self, start_date, end_date, over_ten=False):
        '''
        按商户id 获取收益金额分组
        '''
        condition = " AND channel_id = %s " % self.channel_id

        if over_ten:
            condition += " AND price >= 10 "

        sql = """
            SELECT shop_id, SUM(price), SUM(price*rate)
            FROM admin_order
            WHERE %s <= order_date AND order_date <= %s
        """ + condition + """
            GROUP BY shop_id
        """

        return raw_sql.exec_sql(sql, [start_date, end_date])

    def get_shops(self, owner=None):
        objs = Shop.objects.filter(channel_id=self.channel_id).exclude(owner=u"渠道录入")
        
        if owner:
            objs = objs.filter(owner=owner)

        return objs

    def get_all_shop(self):
        return Shop.objects.filter(channel_id=self.channel_id)

    def get_all_salesman(self):
        '''
        获取所有的业务员
        '''
        return Shop.objects.filter(channel_id=self.channel_id, owner=u"渠道录入")

    def get_active_shops(self, days=3):
        '''
        获取3天内活跃商户id
        '''
        temp_date = datetime.datetime.now() - datetime.timedelta(days=days)

        sql = """
            SELECT shop_id 
            FROM admin_order 
            WHERE order_date > %s AND channel_id = %s
            group by shop_id
        """

        return raw_sql.exec_sql(sql, [temp_date.strftime('%Y-%m-%d') + ' 00:00:00 ', self.channel_id])

    def get_timesharing(self, date, shop_id=None, salesman=None):
        '''
        按小时 获取商户交易金额分组
        '''

        condition = " AND b.channel_id = %s " % self.channel_id
        
        if shop_id:
            condition += " AND b.shop_id = %s " % shop_id
        if salesman:
            condition += " AND a.owner = '%s' " % salesman

        sql = """
            SELECT DATE_FORMAT(b.order_date, "%%H"), SUM(b.price)
            FROM admin_shop a, admin_order b
            WHERE %s <= b.order_date AND b.order_date <= %s
            AND a.shop_id = b.shop_id
        """ + condition + """
            GROUP BY DATE_FORMAT(b.order_date, "%%H")
        """

        return raw_sql.exec_sql(sql, [date + " 00:00:00 ", date + " 23:59:59 "])


    def get_timesharing_detail_group_by_shop_id(self, date, hour, salesman=None):
        '''
        按商户 获取某一时间商户交易金额分组
        '''
        condition = " AND b.channel_id = %s " % self.channel_id

        if salesman:
            condition += " AND a.owner = '%s' " % salesman

        sql = """
            SELECT b.shop_id, SUM(b.price) AS total
            FROM admin_shop a, admin_order b
            WHERE %s <= b.order_date AND b.order_date <= %s
            AND a.shop_id = b.shop_id
        """ + condition + """
            GROUP BY b.shop_id
            ORDER BY total DESC
            LIMIT 0, 10
        """

        return raw_sql.exec_sql(sql, [date+' '+hour+':00:00', date+' '+hour+':59:59'])

    def get_encouragement_detail_group_by_pay_type(self, start_date, end_date):
        '''
        按支付方式 获取交易金额分组
        '''
        condition = " AND b.channel_id = %s " % self.channel_id

        sql = u"""
            SELECT COUNT(b.order_no), SUM(b.price), b.pay_type, b.shop_id
            FROM admin_shop a, admin_order b
            WHERE %s <= b.order_date AND b.order_date <= %s
            AND b.price >= 10
            AND a.shop_id = b.shop_id
            AND a.owner != '渠道录入'
            AND %s <= a.pass_date and a.pass_date <= %s
        """ + condition + """
            GROUP BY b.shop_id, b.pay_type
        """

        return raw_sql.exec_sql(sql, [start_date, end_date, start_date, end_date])

    def get_shops_by_pass_date(self, start_date, end_date, owner=None):
        '''
        '''

        objs = Shop.objects.filter(
            channel_id=self.channel_id, 
            pass_date__range=(start_date, end_date)
        )
        if owner:
            objs = objs.filter(owner=owner)

        return objs

    def get_encouragement_detail_group_by_pay_type_of_shop(self, start_date, end_date, shop_id):
        '''
        按支付方式 获取交易金额分组
        '''
        condition = " AND channel_id = %s " % self.channel_id

        if shop_id:
            condition += " AND shop_id = %s " % shop_id

        sql = u"""
            SELECT COUNT(order_no), SUM(price), pay_type, shop_id
            FROM admin_order b
            WHERE %s <= b.order_date AND b.order_date <= %s
            AND b.price >= 10
        """ + condition + """
            GROUP BY shop_id, pay_type
        """

        return raw_sql.exec_sql(sql, [start_date, end_date])

    def get_shop_count_group_by_salesman(self):
        '''
        按销售人员分组获取店铺数量
        '''
        start_date = '2015-01-01'
        end_date = datetime.datetime.now().strftime('%Y-%m-%d')

        condition = " AND channel_id = %s " % self.channel_id

        sql = u"""
            SELECT count(owner), owner FROM admin_shop
            WHERE %s <= pass_date AND pass_date <= %s
        """ + condition + """
            GROUP BY owner
        """

        return raw_sql.exec_sql(sql, [start_date, end_date])

    def get_shop_count_group_by_salesman_and_month(self, start_date, end_date):
        '''
        按销售人员和月份分组获取店铺数量
        '''
        condition = " AND channel_id = %s " % self.channel_id

        sql = u"""
            SELECT COUNT(owner), owner, DATE_FORMAT(pass_date, "%%Y-%%m")
            FROM admin_shop 
            WHERE %s <= pass_date 
            AND pass_date <= %s 
        """ + condition + """
            GROUP BY owner, DATE_FORMAT(pass_date, "%%Y-%%m")
        """

        return raw_sql.exec_sql(sql, [start_date, end_date])

    def get_lost_shop_group_by_salesman(self, start_date, end_date, latest_order_date):
        '''
        按销售人员和月份分组获取流失店铺数量
        '''
        condition = " AND channel_id = %s " % self.channel_id

        sql = u"""
            SELECT owner, COUNT(name) 
            FROM admin_shop 
            WHERE %s <= pass_date 
            AND pass_date <= %s 
            AND latest_order_date <= %s
        """ + condition + """
            GROUP BY owner
        """

        return raw_sql.exec_sql(sql, [start_date, end_date, latest_order_date]) 

    def get_average_trade_group_by_salesman(self, start_date, end_date):
        '''
        获取各业务员总日估流水
        '''
        condition = " AND channel_id = %s " % self.channel_id

        sql = u"""
            SELECT owner, SUM(average_trade) 
            FROM admin_shop 
            WHERE %s <= pass_date 
            and pass_date <= %s
        """ + condition + """
            GROUP BY owner
        """

        return raw_sql.exec_sql(sql, [start_date, end_date])

    def get_total_order_group_by_salesman(self, start_date, end_date):
        '''
        按销售人员获取流水
        '''
        condition = " AND a.channel_id = %s " % self.channel_id

        sql = u"""
            SELECT a.owner, SUM(b.price) 
            FROM admin_shop a, admin_order b
            WHERE a.shop_id = b.shop_id
            AND %s <= b.order_date
            AND b.order_date <= %s
        """ + condition + """
            GROUP BY a.owner
        """

        return raw_sql.exec_sql(sql, [start_date, end_date]) 


    def get_no_trade_shop_count(self):
        '''
        获取未交易的店铺数量
        '''
        condition = " AND channel_id = %s " % self.channel_id

        sql = u"""
            SELECT shop_id, SUM(price) AS total
            FROM admin_order
            WHERE '2015-05-01 00:00:00' <= order_date
            and order_date <= %s
        """ + condition + """
            GROUP BY shop_id 
            having total <= 100
        """

        return raw_sql.exec_sql(sql, [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')]) 


class UserToChannelBase(object):

    '''
    获取用户可看渠道商
    '''
    def get_channels_of_user(self, user_id):
        from www.misc.account import ACCOUNTS

        channels = []

        for per in UserToChannel.objects.filter(user_id=user_id):
            channels.append([x for x in ACCOUNTS if x['CHANNEL_ID']==per.channel_id][0])

        return channels

    def add_channel(self, email, nick, password, tel, channel_id):
        '''
        添加渠道商
        '''

        # 添加用户
        from www.account import interface
        flag, profile = interface.UserBase().regist_user(
            email = email, 
            nick = nick, 
            password = password, 
            re_password = password, 
            ip = '127.0.0.1', 
            mobilenumber = tel
        )

        # 给用户分配可以查看的渠道
        UserToChannel.objects.create(user_id=profile.id, channel_id=channel_id)
        UserToChannel.objects.create(user_id='e27713a30ae311e79a37a45e60bb9305', channel_id=channel_id)











