# -*- coding: utf-8 -*-
import datetime

from django.db import models

from common.utils import get_summary_from_html_by_sub

class Permission(models.Model):

    '''
    权限类 
    '''
    name = models.CharField(verbose_name=u'权限名称', max_length=64, unique=True)
    code = models.CharField(verbose_name=u'权限代码', max_length=32, unique=True)
    parent = models.ForeignKey('self', verbose_name=u'父权限', related_name="children", null=True)

    def __unicode__(self):
        return '%s-%s' % (self.name, self.code)


class UserPermission(models.Model):

    '''
    用户权限表
    '''
    user_id = models.CharField(verbose_name=u'用户', max_length=32, db_index=True)
    permission = models.ForeignKey(Permission, verbose_name=u'权限')
    create_time = models.DateTimeField(verbose_name=u'创建时间', auto_now_add=True)
    creator = models.CharField(verbose_name=u'创建者', max_length=32)

    class Meta:
        unique_together = [('user_id', 'permission')]


class SensitiveOperationLog(models.Model):
    user_id = models.CharField(verbose_name=u'用户', max_length=32, db_index=True)
    url = models.CharField(verbose_name=u'访问路径', max_length=512)
    data = models.TextField(verbose_name=u'操作数据')
    create_time = models.DateTimeField(verbose_name=u'创建时间', auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-create_time"]


class Shop(models.Model):

    state_choices = ((0, u"停用"), (1, u"正常"))

    shop_id = models.IntegerField(verbose_name=u'商户id', unique=True, db_index=True)
    name = models.CharField(verbose_name=u'商户名称', max_length=128, null=True)
    tel = models.CharField(verbose_name=u'电话', max_length=32, null=True)
    type = models.CharField(verbose_name=u'用户类型', max_length=32, null=True)
    contact = models.CharField(verbose_name=u'联系人', max_length=32, null=True)
    rate = models.DecimalField(verbose_name=u"费率", max_digits=8, decimal_places=4, default=0.0038, null=True)
    owner = models.CharField(verbose_name=u'业务员', max_length=32, null=True)
    pass_date = models.DateTimeField(verbose_name=u'通过时间', null=True)
    percentage = models.DecimalField(verbose_name=u"费率", max_digits=8, decimal_places=2, default=0.3, null=True)
    latest_order_date = models.DateTimeField(verbose_name=u'最后交易时间', null=True)
    channel_id = models.IntegerField(verbose_name=u'渠道id', db_index=True, null=True)

    state = models.IntegerField(verbose_name=u"状态", default=1, db_index=True, choices=state_choices)
    create_time = models.DateTimeField(verbose_name=u'创建时间', auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-pass_date"]

    def is_inactive(self):
        '''
        是否非活跃
        '''
        if self.latest_order_date:
            return (datetime.datetime.now() - self.latest_order_date).days >= 3
        else:
            return False


class Order(models.Model):

    shop_id = models.IntegerField(verbose_name=u'商户id', db_index=True)
    order_no = models.CharField(verbose_name=u'交易查询号', max_length=64, unique=True, null=True)
    order_date = models.DateTimeField(verbose_name=u'交易日期', db_index=True, null=True)
    card_no = models.CharField(verbose_name=u'交易卡号', max_length=64, null=True)
    price = models.DecimalField(verbose_name=u"交易金额", max_digits=10, decimal_places=2, null=True, db_index=True)
    type = models.CharField(verbose_name=u'交易类型', max_length=64, null=True)
    state = models.CharField(verbose_name=u'交易状态', max_length=64, null=True)
    rate = models.DecimalField(verbose_name=u"费率", max_digits=8, decimal_places=4, default=0.0038, null=True)
    channel_id = models.IntegerField(verbose_name=u'渠道id', db_index=True, null=True)

    create_time = models.DateTimeField(verbose_name=u'创建时间', auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-order_date"]


class UserToChannel(models.Model):
    '''
    用户与渠道的对照表
    '''

    user_id = models.CharField(verbose_name=u'用户', max_length=32)
    channel_id = models.IntegerField(verbose_name=u'商户id')






