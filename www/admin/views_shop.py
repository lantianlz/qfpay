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

    orders = ShopBase(shop.channel_id).get_order_list(start_date, end_date, None, shop_id).values()
    total = sum([x['price'] for x in orders])
    order_count = len(orders)
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

@member_required
def choose_channel(request, template_name='pc/admin/choose_channel.html'):

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
    today = datetime.datetime.now()
    start_date = today.replace(day=1).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

@member_required
@channel_required
def per_shop(request, shop_id, template_name='pc/admin/per_shop.html'):
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
    today = datetime.datetime.now()
    start_date = today.replace(day=1).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

@member_required
@channel_required
def inactive_shops(request, template_name='pc/admin/inactive_shops.html'):

    shops = ShopBase(request.session['CHANNEL_ID']).get_shops().order_by('latest_order_date')

    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

@member_required
@channel_required
def timesharing(request, template_name="pc/admin/timesharing.html"):
    date = request.GET.get('date', datetime.datetime.now().strftime('%Y-%m-%d'))
    shop_id = request.GET.get('shop_id')
    if shop_id:
        shop = ShopBase(request.session['CHANNEL_ID']).get_shop_by_id(shop_id)
        
    return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def _get_shop_info(channel_id):
    shop_base = ShopBase(channel_id)

    # 商户与归属人对照
    dict_shop_info = {}
    for x in shop_base.get_all_shop().values('shop_id', 'owner', 'name'):
        dict_shop_info[x['shop_id']] = {'owner': x['owner'], 'name': x['name']}

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

    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    start_date, end_date = utils.get_date_range(start_date, end_date)

    # 商户信息字典
    dict_shop_info = _get_shop_info(request.session['CHANNEL_ID'])

    result = shop_base.get_shop_sort(start_date, end_date)
    max_total = decimal.Decimal(result[0][3]) if len(result) > 0 else 0

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
            'owner': dict_shop_info[x[0]]['owner']
        })
        active_shops.append(x[0])

    for x in shop_base.get_shops():
        if x.shop_id not in active_shops:
            data.append({
                'shop_id': x.shop_id,
                'name': x.name,
                'count': 0,
                'total': 0,
                'average': 0,
                'rate': 0,
                'owner': dict_shop_info[x.shop_id]['owner']
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

    over_ten = request.POST.get('over_ten', 'false')
    over_ten = False if over_ten == 'false' else True
    shop_id = request.POST.get('shop_id')
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    start_date, end_date = utils.get_date_range(start_date, end_date)

    count_result = shop_base.get_order_count(start_date, end_date, over_ten, shop_id)
    price_result = shop_base.get_order_price(start_date, end_date, over_ten, shop_id)

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

    price_sort = request.POST.get('price_sort', 'false')
    price_sort = False if price_sort == 'false' else True
    shop_id = request.POST.get('shop_id')
    page_index = int(request.REQUEST.get('page_index'))
    start_date = request.REQUEST.get('start_date')
    end_date = request.REQUEST.get('end_date')
    start_date, end_date = utils.get_date_range(start_date, end_date)

    # 商户信息字典
    dict_shop_info = _get_shop_info(request.session['CHANNEL_ID'])

    objs = shop_base.get_order_list(start_date, end_date, price_sort, shop_id)

    page_objs = page.Cpt(objs, count=15, page=page_index).info

    num = 15 * (page_index - 1)
    for x in page_objs[0]:
        num += 1

        data.append({
            'num': num,
            'name': dict_shop_info[x.shop_id]['name'],
            'order_no': x.order_no,
            'card_no': x.card_no,
            'order_date': str(x.order_date),
            'price': str(x.price),
            'type': x.type,
            'state': x.state
        })


    return HttpResponse(
        json.dumps({'data': data, 'page_count': page_objs[4], 'total_count': page_objs[5]}),
        mimetype='application/json'
    )


def get_salesman_statistics_data(request):
    shop_base = ShopBase(request.session['CHANNEL_ID'])

    start_date = request.REQUEST.get('start_date')
    end_date = request.REQUEST.get('end_date')
    start_date, end_date = utils.get_date_range(start_date, end_date)

    # 商户金额字典
    dict_shop_2_total = {}
    for x in shop_base.get_order_total_group_by_shop(start_date, end_date):
        if not dict_shop_2_total.has_key(x['shop_id']):
            dict_shop_2_total[x['shop_id']] = x['price__sum']
    
    # 商户收益字典
    dict_shop_2_rate = {}
    for x in shop_base.get_order_rate_group_by_shop(start_date, end_date):
        if not dict_shop_2_rate.has_key(x[0]):
            dict_shop_2_rate[x[0]] = x[1]

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
        _percentage = float(dict_salesman_2_percentage.get(k, 0))
        # 税后利润
        _profit_after_tax = _profit/1.03

        if _total <= 0:
            continue

        xdata.append(k)
        ydata.append({'name': k, 'value': _total})
        data.append({
            'name': k,
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
    shop_id = request.REQUEST.get('shop_id')

    xdata = []
    ydata = []
    all_total = 0
    average_total = 0
    active_hours = 0

    timesharing_data = {}
    for x in ShopBase(request.session['CHANNEL_ID']).get_timesharing(date, shop_id):
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
    hour = hour or '00'

    for x in shop_base.get_timesharing_detail_group_by_shop_id(date, hour):
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




