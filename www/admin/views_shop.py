# -*- coding: utf-8 -*-

import json
import datetime
import decimal
import urllib
from django.contrib import auth
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response

from common import utils, page
from misc.decorators import staff_required, common_ajax_response, verify_permission, member_required, channel_required

from www.admin.interface import ShopBase, UserToChannelBase

def order_list(request, template_name='pc/admin/order_list.html'):

    shop_id = request.REQUEST.get('shop_id')

    shop = ShopBase('').get_shop_by_id(shop_id)

    today = datetime.datetime.now()
    tomorrow = (today + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    today = today.strftime('%Y-%m-%d')

    start_date = request.POST.get('start_date')
    start_date = start_date if start_date else (today + ' 00:00')
    end_date = request.POST.get('end_date')
    end_date = end_date if end_date else (tomorrow + ' 00:00')

    orders = ShopBase(shop.channel_id).get_order_list(start_date, end_date, None, shop_id)
    total = sum([x[4] for x in orders])
    order_count = len(orders)
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

@member_required
def choose_channel(request, template_name='pc/admin/choose_channel.html'):
    '''
    渠道选择
    '''
    channels = UserToChannelBase().get_channels_of_user(request.user.id)

    channel_id = request.GET.get('channel')
    if channel_id:
        request.session['CHANNEL_ID'] = channel_id
        request.session['CHANNEL_NAME'] = [x for x in channels if x['CHANNEL_ID']==int(channel_id)][0]['USERNAME']
        return HttpResponseRedirect('/admin/shop')

    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

@member_required
@channel_required
def shop(request, template_name='pc/admin/shop.html'):
    '''
    商户统计
    '''
    today = datetime.datetime.now()
    start_date = today.replace(day=1).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    salesman = request.REQUEST.get('salesman', '')
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

@member_required
@channel_required
def per_shop(request, shop_id, template_name='pc/admin/per_shop.html'):
    '''
    单店统计
    '''
    shop = ShopBase(request.session['CHANNEL_ID']).get_shop_by_id(shop_id)
    today = datetime.datetime.now()

    start_date = request.GET.get('start_date')
    start_date = start_date or today.replace(day=1).strftime('%Y-%m-%d')
    end_date = request.GET.get('end_date')
    end_date = end_date or today.strftime('%Y-%m-%d')
    
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

@member_required
@channel_required
def salesman(request, template_name='pc/admin/salesman.html'):
    '''
    业务员统计
    '''
    today = datetime.datetime.now()
    start_date = today.replace(day=1).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

@member_required
@channel_required
def inactive_shops(request, template_name='pc/admin/inactive_shops.html'):
    '''
    风险流失统计
    '''
    shop_base = ShopBase(request.session['CHANNEL_ID'])
    shops = shop_base.get_shops().order_by('latest_order_date')

    no_trade_count = len(shop_base.get_no_trade_shop_count())

    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

@member_required
@channel_required
def timesharing(request, template_name="pc/admin/timesharing.html"):
    '''
    分时统计
    '''
    date = request.GET.get('date', datetime.datetime.now().strftime('%Y-%m-%d'))
    shop_id = request.GET.get('shop_id')
    salesman = request.GET.get('salesman')
    if shop_id:
        shop = ShopBase(request.session['CHANNEL_ID']).get_shop_by_id(shop_id)
        
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

@member_required
@channel_required
def encouragement(request, template_name="pc/admin/encouragement.html"):
    '''
    激励统计
    '''
    today = datetime.datetime.now()
    start_date = today.replace(day=1).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

@member_required
@channel_required
def performance(request, template_name="pc/admin/performance.html"):
    '''
    业务员考核统计
    '''
    date = datetime.datetime.now().strftime('%Y-%m')
    
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))



def _get_shop_info(channel_id):
    shop_base = ShopBase(channel_id)

    # 商户与归属人对照
    dict_shop_info = {}
    for x in shop_base.get_all_shop().values('shop_id', 'owner', 'name', 'tel', 'pass_date'):
        dict_shop_info[x['shop_id']] = {
            'owner': x['owner'], 
            'name': x['name'], 
            'tel': x['tel'],
            'pass_date': str(x['pass_date'])[:10]
        }

    return dict_shop_info

def get_shop_sort(request):
    shop_base = ShopBase(request.session['CHANNEL_ID'])

    all_shop_count = 0
    active_shop_count = 0
    all_order_count = 0
    average_order_count = 0
    all_order_price = 0
    average_order_price = 0
    active_shops = []
    data = []

    # 按通过时间排序
    pass_date_sort = request.REQUEST.get('pass_date_sort')
    pass_date_sort = False if pass_date_sort == 'false' else True
    # 销售员
    salesman = request.REQUEST.get('salesman', '')

    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    start_date, end_date = utils.get_date_range(start_date, end_date)

    # 商户信息字典
    dict_shop_info = _get_shop_info(request.session['CHANNEL_ID'])

    result = shop_base.get_shop_sort(start_date, end_date, pass_date_sort, salesman)
    max_total = decimal.Decimal(result[0][3]) if len(result) > 0 else 0
    max_total = max([x[3] for x in result]) if len(result) > 0 else 0

    for x in result:

        total = decimal.Decimal(x[3])

        # 统计店铺总数
        all_shop_count += 1
        # 统计总订单数
        all_order_count += x[2]
        # 统计总交易额
        all_order_price += total

        # 交易金额大于50才算是有效商户
        if total >= 50:
            active_shop_count += 1
        
        data.append({
            'shop_id': x[0],
            'name': x[1],
            'count': x[2],
            'total': str(x[3]),
            'average': round(x[3] / x[2], 2),
            'rate': round(total / max_total * 100, 1) if max_total != 0 else 0,
            'owner': dict_shop_info[x[0]]['owner'],
            'pass_date': str(x[4])[:10]
        })
        active_shops.append(x[0])

    for x in shop_base.get_shops(salesman):
        if x.shop_id not in active_shops:
            data.append({
                'shop_id': x.shop_id,
                'name': x.name,
                'count': 0,
                'total': 0,
                'average': 0,
                'rate': 0,
                'owner': dict_shop_info[x.shop_id]['owner'],
                'pass_date': str(x.pass_date)[:10]
            })

    average_order_count = (all_order_count / active_shop_count) if active_shop_count != 0 else 0
    average_order_price = (all_order_price / active_shop_count) if active_shop_count != 0 else 0

    return HttpResponse(
        json.dumps({
            'data': data,
            'all_shop_count': all_shop_count,
            'all_order_count': all_order_count,
            'active_shop_count': active_shop_count,
            'average_order_count': average_order_count,
            'all_order_price': str(all_order_price),
            'average_order_price': str(average_order_price)
        }),
        mimetype='application/json'
    )


def get_order_statistic_data(request):
    shop_base = ShopBase(request.session['CHANNEL_ID'])

    x_count_data = []
    y_count_data = []
    x_price_data = []
    y_price_data = []
    all_shop_count = 0
    all_order_count = 0
    average_order_count = 0
    all_order_price = 0
    average_order_price = 0

    # 销售员
    salesman = request.REQUEST.get('salesman', '')
    over_ten = request.POST.get('over_ten', 'false')
    over_ten = False if over_ten == 'false' else True
    shop_id = request.POST.get('shop_id')
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    start_date, end_date = utils.get_date_range(start_date, end_date)

    count_result = shop_base.get_order_count(start_date, end_date, over_ten, shop_id, salesman)
    price_result = shop_base.get_order_price(start_date, end_date, over_ten, shop_id, salesman)

    for x in count_result:
        all_shop_count += 1
        x_count_data.append(x[0])
        y_count_data.append(x[1])
        all_order_count += x[1]
    average_order_count = (all_order_count / all_shop_count) if all_shop_count != 0 else 0

    for x in price_result:
        x_price_data.append(x[0])
        y_price_data.append(str(x[1]))
        all_order_price += x[1]
    average_order_price = (all_order_price / all_shop_count) if all_shop_count != 0 else 0

    return HttpResponse(
        json.dumps({
            'x_count_data': x_count_data, 
            'y_count_data': y_count_data,
            'all_order_count': all_order_count, 
            'average_order_count': average_order_count,
            'x_price_data': x_price_data,
            'y_price_data': y_price_data,
            'all_order_price': str(all_order_price), 
            'average_order_price': str(average_order_price)
        }),
        mimetype='application/json'
    )


def get_order_list(request):
    shop_base = ShopBase(request.session['CHANNEL_ID'])

    data = []

    salesman = request.REQUEST.get('salesman', '')
    price_sort = request.POST.get('price_sort', 'false')
    price_sort = False if price_sort == 'false' else True
    shop_id = request.POST.get('shop_id')
    page_index = int(request.REQUEST.get('page_index'))
    start_date = request.REQUEST.get('start_date')
    end_date = request.REQUEST.get('end_date')
    start_date, end_date = utils.get_date_range(start_date, end_date)

    # 商户信息字典
    # dict_shop_info = _get_shop_info(request.session['CHANNEL_ID'])

    objs = shop_base.get_order_list(start_date, end_date, price_sort, shop_id, salesman)

    page_objs = page.Cpt(objs, count=15, page=page_index).info

    num = 15 * (page_index - 1)
    for x in page_objs[0]:
        num += 1

        data.append({
            'num': num,
            'name': x[0],
            'order_no': x[1],
            'card_no': x[2],
            'order_date': str(x[3]),
            'price': str(x[4]),
            'type': x[5],
            'state': x[6]
        })


    return HttpResponse(
        json.dumps({'data': data, 'page_count': page_objs[4], 'total_count': page_objs[5]}),
        mimetype='application/json'
    )


def _get_percentage(total, percentage):
    '''
    0 - 100万 ---> 0.3
    100万 - 300万 ---> 0.4
    300万+ ---> 0.5
    '''
    _percentage = 0.3

    # 默认为0.3，大于0.3则表示特殊处理，直接使用
    if 0.3 <= percentage:
        return float(percentage)

    if 1000000 < total and total <= 3000000:
        percentage = 0.4

    if 3000000 < total:
        percentage = 0.5

    return percentage

def get_salesman_statistics_data(request):
    '''
    业务员交易统计
    '''

    shop_base = ShopBase(request.session['CHANNEL_ID'])

    start_date = request.REQUEST.get('start_date')
    end_date = request.REQUEST.get('end_date')
    over_ten = request.POST.get('over_ten', 'false')
    over_ten = False if over_ten == 'false' else True
    start_date, end_date = utils.get_date_range(start_date, end_date)

    # 销售员对应商户数量
    dict_salesman_2_shop_count = {}
    for x in shop_base.get_shop_count_group_by_salesman():
        if not dict_salesman_2_shop_count.has_key(x[1]):
            dict_salesman_2_shop_count[x[1]] = x[0]
    
    # 商户金额字典
    dict_shop_2_total = {}
    # 商户收益字典
    dict_shop_2_rate = {}
    for x in shop_base.get_order_total_and_rate_group_by_shop(start_date, end_date, over_ten):
        if not dict_shop_2_total.has_key(x[0]):
            dict_shop_2_total[x[0]] = x[1]

        if not dict_shop_2_rate.has_key(x[0]):
            dict_shop_2_rate[x[0]] = x[2]

    # 业务员与商户对照
    dict_salesman_2_shop = {}
    for x in shop_base.get_all_shop():
        if not dict_salesman_2_shop.has_key(x.owner):
            dict_salesman_2_shop[x.owner] = [0, 0, x.percentage]
        # 总额
        dict_salesman_2_shop[x.owner][0] += dict_shop_2_total.get(x.shop_id, 0)
        # 收益
        dict_salesman_2_shop[x.owner][1] += dict_shop_2_rate.get(x.shop_id, 0)
    
    # 业务员与提成比例对照
    dict_salesman_2_percentage = {}
    for x in shop_base.get_all_salesman():
        dict_salesman_2_percentage[x.contact] = x.percentage

    # 业务员总流失单对照
    today = datetime.datetime.now()
    latest_order_date = today - datetime.timedelta(days=3)
    latest_order_date = latest_order_date.strftime('%Y-%m-%d %H:%M:%S')
    dict_salesman_2_lost_shop = {}
    for x in shop_base.get_lost_shop_group_by_salesman(
        '2015-01-01 00:00:00', 
        today.strftime('%Y-%m-%d %H:%M:%S'),
        latest_order_date
    ):
        dict_salesman_2_lost_shop[x[0]] = x[1]

    # 图表数据
    xdata = []
    ydata = []
    data = []
    all_total = 0
    all_profit = 0
    all_percentage_price = 0
    for k in dict_salesman_2_shop.keys():
        # 交易金额
        _total = float(dict_salesman_2_shop[k][0])
        # 交易利润，排除掉 业务员刷卡的
        _profit = float(dict_salesman_2_shop[k][1]) if k != u'渠道录入' else 0
        # 提成比例
        _percentage = _get_percentage(_total, dict_salesman_2_percentage.get(k, 0.3)) if k != u'渠道录入' else 0
        # 税后利润
        _profit_after_tax = _profit/1.03

        if _total <= 0:
            continue

        xdata.append(k)
        ydata.append({'name': k, 'value': _total})
        data.append({
            'name': k,
            'shop_count': dict_salesman_2_shop_count.get(k, 0),
            'lost_count': dict_salesman_2_lost_shop.get(k, 0),
            'total': _total,
            'profit': _profit,
            'profit_after_tax': _profit_after_tax,
            'percentage': _percentage,
            'percentage_price': _profit_after_tax * _percentage
        })
        all_total += _total
        all_profit += _profit
        all_percentage_price += _profit_after_tax * _percentage

    ydata.sort(key=lambda k: k['value'], reverse=True)
    xdata = [x['name'] for x in ydata]
    data.sort(key=lambda k: k['total'], reverse=True)

    return HttpResponse(
        json.dumps({
            'xdata': xdata[:10], 'ydata': ydata[:10], 'data': data,
            'all_total': all_total,
            'all_profit': all_profit,
            'all_percentage_price': all_percentage_price
        }),
        mimetype='application/json'
    )



def get_timesharing_statistics_data(request):

    date = request.REQUEST.get('date')
    shop_id = request.REQUEST.get('shop_id', '')
    salesman = request.REQUEST.get('salesman', '')

    xdata = []
    ydata = []
    all_total = 0
    average_total = 0
    active_hours = 0

    timesharing_data = {}
    for x in ShopBase(request.session['CHANNEL_ID']).get_timesharing(date, shop_id, salesman):
        timesharing_data[int(x[0])] = x[1]
        all_total += x[1]
        active_hours += 1

    for x in range(24):
        xdata.append(x)
        ydata.append(float(timesharing_data.get(x, 0)))

    average_total = (all_total / active_hours) if active_hours else 0

    return HttpResponse(
        json.dumps({
            'xdata': xdata, 'ydata': ydata,
            'all_total': float(all_total),
            'average_total': float(average_total)
        }),
        mimetype='application/json'
    )

def get_timesharing_detail_data(request):
    shop_base = ShopBase(request.session['CHANNEL_ID'])

    data = []

    date = request.REQUEST.get('date')
    hour = request.REQUEST.get('hour')
    salesman = request.REQUEST.get('salesman', '')
    hour = hour or '00'

    for x in shop_base.get_timesharing_detail_group_by_shop_id(date, hour, salesman):
        data.append({
            'shop_id': x[0],
            'name': shop_base.get_shop_by_id(x[0]).name,
            'total': float(x[1])
        })

    return HttpResponse(
        json.dumps({
            'data': data
        }),
        mimetype='application/json'
    )


def _get_encouragement(per_count):
    '''
    激励金额规则
    '''
    if 20 <= per_count and per_count < 40:
        return 20
    elif 40 <= per_count and per_count < 60:
        return 50
    elif 60 <= per_count:
        return 120
    else:
        return 0
def get_encouragement_data(request):
    '''
    统计激励金 按钱方规则
    '''
    total_encouragement = 0
    all_pay_count = 0
    all_pay_total = 0
    data = {}

    shop_base = ShopBase(request.session['CHANNEL_ID'])

    start_date = request.REQUEST.get('start_date')
    end_date = request.REQUEST.get('end_date')
    start_date, end_date = utils.get_date_range(start_date, end_date)

    # 商户信息字典
    dict_shop_info = _get_shop_info(request.session['CHANNEL_ID'])

    for x in shop_base.get_encouragement_detail_group_by_pay_type(start_date, end_date):
        key = x[3]
        if not data.has_key(key):
            data[key] = {
                'shop_id': key,
                'name': dict_shop_info[key]['name'],
                'tel': dict_shop_info[key]['tel'],
                'pass_date': dict_shop_info[key]['pass_date'],
                'wx_pay_count': 0,
                'wx_pay_total': 0,
                'alipay_pay_count': 0,
                'alipay_pay_total': 0,
                'pay_count': 0,
                'pay_total': 0,
                'encouragement': 0
            }

        _count = x[0]
        _total = float(x[1])

        # 微信
        if x[2] == 1:
            data[key]['wx_pay_count'] += _count
            data[key]['wx_pay_total'] += _total
        else:
            data[key]['alipay_pay_count'] += _count
            data[key]['alipay_pay_total'] += _total

        data[key]['pay_count'] += _count
        data[key]['pay_total'] += _total

    for key in data.keys():
        data[key]['encouragement'] = _get_encouragement(data[key]['pay_count'])
        total_encouragement += data[key]['encouragement']
        all_pay_count += data[key]['pay_count']
        all_pay_total += data[key]['pay_total']

    data = data.values()
    data.sort(key=lambda x: x['encouragement'], reverse=True)

    return HttpResponse(
        json.dumps({
            'data': data,
            'all_pay_count': all_pay_count,
            'all_pay_total': all_pay_total,
            'total_encouragement': total_encouragement
        }),
        mimetype='application/json'
    )


def get_encouragement_data_2(request):
    '''
    统计激励金 按新规则
    '''
    total_encouragement = 0
    all_pay_count = 0
    all_pay_total = 0
    data = {}

    shop_base = ShopBase(request.session['CHANNEL_ID'])

    start_date = request.REQUEST.get('start_date')
    end_date = request.REQUEST.get('end_date')
    start_date, end_date = utils.get_date_range(start_date, end_date)

    # 商户信息字典
    dict_shop_info = _get_shop_info(request.session['CHANNEL_ID'])

    for x in shop_base.get_shops_by_pass_date(start_date, end_date):
        if x.owner == u'渠道录入':
            continue
        # 获取该店通过日期之后 30 天内交易数据
        for y in shop_base.get_encouragement_detail_group_by_pay_type_of_shop(
            (x.pass_date).strftime('%Y-%m-%d'), 
            (x.pass_date + datetime.timedelta(days=30)).strftime('%Y-%m-%d'), 
            x.shop_id
        ):
            key = x.shop_id
            if not data.has_key(key):
                data[key] = {
                    'shop_id': key,
                    'name': dict_shop_info[key]['name'],
                    'tel': dict_shop_info[key]['tel'],
                    'pass_date': dict_shop_info[key]['pass_date'],
                    'wx_pay_count': 0,
                    'wx_pay_total': 0,
                    'alipay_pay_count': 0,
                    'alipay_pay_total': 0,
                    'pay_count': 0,
                    'pay_total': 0,
                    'encouragement': 0
                }

            _count = y[0]
            _total = float(y[1])

            # 微信
            if y[2] == 1:
                data[key]['wx_pay_count'] += _count
                data[key]['wx_pay_total'] += _total
            else:
                data[key]['alipay_pay_count'] += _count
                data[key]['alipay_pay_total'] += _total

            data[key]['pay_count'] += _count
            data[key]['pay_total'] += _total

    for key in data.keys():
        data[key]['encouragement'] = _get_encouragement(data[key]['pay_count'])
        total_encouragement += data[key]['encouragement']
        all_pay_count += data[key]['pay_count']
        all_pay_total += data[key]['pay_total']

    data = data.values()
    data.sort(key=lambda x: x['encouragement'], reverse=True)

    return HttpResponse(
        json.dumps({
            'data': data,
            'all_pay_count': all_pay_count,
            'all_pay_total': all_pay_total,
            'total_encouragement': total_encouragement
        }),
        mimetype='application/json'
    )



def get_performance_data(request):
    '''
    业务员考核统计
    '''
    import calendar

    today = datetime.datetime.now()
    date = request.REQUEST.get('date')
    date = datetime.datetime.strptime(date, '%Y-%m')

    shop_base = ShopBase(request.session['CHANNEL_ID'])

    # 业务员总开单数字典
    dict_salesman_2_shop_count = {}
    for x in shop_base.get_shop_count_group_by_salesman():
        if not dict_salesman_2_shop_count.has_key(x[1]):
            dict_salesman_2_shop_count[x[1]] = x[0]

    # 获取两个月内各个业务员开单情况
    start_date = date - datetime.timedelta(days=1)
    start_date = start_date.replace(day=1).strftime('%Y-%m-%d')
    a, month_range = calendar.monthrange(date.year, date.month)
    end_date = datetime.datetime(date.year, date.month, month_range).strftime('%Y-%m-%d')

    this_month = end_date[:7]
    last_month = start_date[:7]

    dict_salesman_2_shop_of_month = {}
    for x in shop_base.get_shop_count_group_by_salesman_and_month(start_date, end_date+' 23:59:59'):
        if not dict_salesman_2_shop_of_month.has_key(x[1]):
            dict_salesman_2_shop_of_month[x[1]] = {this_month: 0, last_month: 0}
        dict_salesman_2_shop_of_month[x[1]][x[2]] += x[0]

    # 获取指定时间各个业务员流失单
    start_date = '%s-%s-%s 00:00:00' % (date.year, date.month, 1)
    end_date = '%s-%s-%s 23:59:59' % (date.year, date.month, month_range)
    latest_order_date = today - datetime.timedelta(days=3)
    latest_order_date = latest_order_date.strftime('%Y-%m-%d %H:%M:%S')
    dict_salesman_2_lost_shop = {}
    for x in shop_base.get_lost_shop_group_by_salesman(start_date, end_date, latest_order_date):
        if not dict_salesman_2_lost_shop.has_key(x[0]):
            dict_salesman_2_lost_shop[x[0]] = x[1]

    # 获取各业务员总新增日估流水
    dict_salesman_2_average_trade = {}
    for x in shop_base.get_average_trade_group_by_salesman(start_date, end_date):
        if not dict_salesman_2_average_trade.has_key(x[0]):
            dict_salesman_2_average_trade[x[0]] = [float(x[1] or 0), float(x[1] or 0) * 30]

    # 获取业务员总销售流水
    dict_shop_2_total = {}
    for x in shop_base.get_total_order_group_by_salesman(start_date, end_date):
        if not dict_shop_2_total.has_key(x[0]):
            dict_shop_2_total[x[0]] = float(x[1])

    data = []
    for k in dict_salesman_2_shop_count.keys():

        if k == u"渠道录入":
            continue

        data.append({
            'name': k, 
            'this_month_count': dict_salesman_2_shop_of_month[k][this_month] if dict_salesman_2_shop_of_month.has_key(k) else 0,
            'last_month_count': dict_salesman_2_shop_of_month[k][last_month] if dict_salesman_2_shop_of_month.has_key(k) else 0,
            'all_count': dict_salesman_2_shop_count.get(k, 0),
            'lost_count': dict_salesman_2_lost_shop.get(k, 0),
            'average_trade': dict_salesman_2_average_trade[k][0] if dict_salesman_2_average_trade.has_key(k) else 0,
            'average_trade_of_month': dict_salesman_2_average_trade[k][1] if dict_salesman_2_average_trade.has_key(k) else 0,
            'total': dict_shop_2_total[k] if dict_shop_2_total.has_key(k) else 0
        })

    data.sort(key=lambda k: k['total'], reverse=True)

    all_new = 0
    all_lost = 0
    all_lost_rate = 0
    for x in data:
        all_new += x['this_month_count']
        all_lost += x['lost_count']

    all_lost_rate = float(all_lost)/all_new*100 if all_new else 0

    return HttpResponse(
        json.dumps({
            'data': data,
            'all_new': all_new,
            'all_lost': all_lost,
            'all_lost_rate': all_lost_rate
        }),
        mimetype='application/json'
    )


def get_new_shop_of_current_month(request):
    import calendar

    owner = request.REQUEST.get('owner', None)
    date = request.REQUEST.get('date')
    date = datetime.datetime.strptime(date, '%Y-%m')
    a, month_range = calendar.monthrange(date.year, date.month)
    start_date = '%s-%s-%s 00:00:00' % (date.year, date.month, 1)
    end_date = '%s-%s-%s 23:59:59' % (date.year, date.month, month_range)

    shop_base = ShopBase(request.session['CHANNEL_ID'])

    data = []
    all_reward = 0
    for shop in shop_base.get_shops_by_pass_date(start_date, end_date, owner):
        reward = 0
        if 100 < shop.average_trade and shop.average_trade <= 1000:
            reward = 10
        if shop.average_trade > 1000:
            reward = 20

        data.append({
            'shop_id': shop.shop_id,
            'name': shop.name,
            'pass_date': str(shop.pass_date)[:10],
            'owner': shop.owner,
            'latest_order_date': str(shop.latest_order_date),
            'average_trade': float(shop.average_trade),
            'reward': reward
        })

        all_reward += reward

    return HttpResponse(
        json.dumps({
            'data': data,
            'all_reward': all_reward
        }),
        mimetype='application/json'
    )


















