# coding: utf-8
import requests, random, time, os, sys, datetime, decimal, traceback
from pyquery import PyQuery as pq

from requests.packages.urllib3.exceptions import InsecureRequestWarning, SNIMissingWarning, InsecurePlatformWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(SNIMissingWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)

# 引入父目录来引入其他模块
SITE_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.extend([os.path.abspath(os.path.join(SITE_ROOT, '../')),
                 os.path.abspath(os.path.join(SITE_ROOT, '../../')),
                 os.path.abspath(os.path.join(SITE_ROOT, '../../www')),
                 ])
os.environ['DJANGO_SETTINGS_MODULE'] = 'www.settings'

from www.admin.models import Shop, Order

class Spider(object):

    # User-Agent
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
    # 线程每次请求之后的休眠时间
    SLEEP_TIME = 0.8
    # 登录URL
    LOGIG_URL = u"https://qfpay.com/qudao/channel_login"
    # 生成验证码URL
    CAPTCHA_URL = u"https://qfpay.com/qudao/getcaptcha?t=" + str(random.random())
    # 获取验证码图片URL
    CAPTCHA_IMAGE_URL = u"https://qfpay.com/qudao/captcha/image/"
    # 商户列表URL
    SHOP_URL = u"https://qfpay.com/qudao/manage"
    # 流水列表
    ORDER_URL = u"https://qfpay.com/qudao/history/"

    def __init__(self, channel_id, username, password, cost, default_rate):
        self.CHANNEL_ID = channel_id
        self.USERNAME = username
        self.PASSWORD = password
        self.COST = cost
        self.DETAULT_RATE = default_rate

        self.session = requests.Session()

        # 商户的费率字典
        self.DICT_SHOP_2_RATE = {}
        

    def login(self):
        '''
        登陆
        '''
        print u"访问登陆界面..."
        self.session.get(url=self.LOGIG_URL, headers={"User-Agent": self.USER_AGENT}, verify=False)
        time.sleep(self.SLEEP_TIME)

        print u"访问生成验证码链接..."
        req = self.session.get(url=self.CAPTCHA_URL, headers={"User-Agent": self.USER_AGENT, "Referer": self.LOGIG_URL})
        captcha_key = req.json()["key"]
        print u"浏览器打开: " + self.CAPTCHA_IMAGE_URL + captcha_key

        # 手动输入验证码
        captcha = raw_input("请输入验证码: ")
        
        # 登陆
        payload = {"username": self.USERNAME, "password": self.PASSWORD, "captcha": captcha, "captchakey": captcha_key}
        req = self.session.post(url=self.LOGIG_URL, data=payload, headers={"User-Agent": self.USER_AGENT, "Referer": self.LOGIG_URL})
        if req.text.find(u'验证码错误') > -1:
            print u'验证码错误'
            return False
        else:
            print u"登陆成功！"
            print ''
            time.sleep(self.SLEEP_TIME)
            return True


    def sync_shop(self, init):
        '''
        同步商户
        '''

        # 获取最后添加的商户id
        latest_shop_id = 0
        # if Shop.objects.count() > 0:
        #     latest_shop_id = Shop.objects.all().order_by('-shop_id')[0].shop_id

        shop_infos = []
        page_index = 1
        count = 0
        while(page_index > 0):
            infos, page_index = self._sync_shop_per_page(page_index, latest_shop_id)
            shop_infos += infos

            if not init:
                count += 1
                if count >= 4:
                    break

        print u'获取商户列表完成，总共更新[ %s ]家商户。' % len(shop_infos)
        print ''

        # 获取该渠道商下每个商户对应的比率
        for x in Shop.objects.filter(channel_id = self.CHANNEL_ID):
            self.DICT_SHOP_2_RATE[x.shop_id] = x.rate
        return shop_infos

    def _sync_shop_per_page(self, page_index, latest_shop_id):
        '''
        获取每页的数据
        '''
        req = self.session.get(
            url = self.SHOP_URL + u"?page=%s&startTime=&endTime=&query=&deactive=0" % page_index, 
            headers = {"User-Agent": self.USER_AGENT, "Referer": self.SHOP_URL}
        )
        time.sleep(self.SLEEP_TIME)
        doc = pq(req.text)

        # print u'抓取第[ %s ]页商户信息...' % page_index
        infos = []
        is_break = False
        for tr in doc('#example tbody tr'):
            info = {
                'name': tr.findall('td')[0].text,
                'tel': tr.findall('td')[1].text,
                'type': tr.findall('td')[2].text,
                'contact': tr.findall('td')[3].text,
                'rate': tr.findall('td')[4].text,
                'owner': tr.findall('td')[5].text,
                'pass_date': tr.findall('td')[6].text,
                'shop_id': tr.findall('td')[7].findall('a')[0].get('href').split('/')[-1]
            }
            # print info

            # ==== 保存数据 ====
            shop_id = int(info['shop_id'])
            # 是否到达上次更新点
            # if shop_id <= latest_shop_id:
            #     is_break = True
            #     break

            if Shop.objects.filter(shop_id = info['shop_id']).count() > 0:
                continue

            Shop.objects.create(
                shop_id = info['shop_id'],
                name = info['name'],
                tel = info['tel'],
                type = info['type'],
                contact = info['contact'],
                rate = self.DETAULT_RATE, # 默认0.38费率
                owner = info['owner'],
                pass_date = info['pass_date'],
                channel_id = self.CHANNEL_ID
            )

            infos.append(info)

        print u'第[ %s ]页商户信息抓取完毕。' % page_index
        print ''
            
        if is_break:
            return infos, -1

        # 判断是否还有下一页
        next_links = doc('.pagination li a')
        index = -1
        for i in range(len(next_links)):
            # 找到当前a标签
            if next_links[i].text == str(page_index):
                # 是否还有下一页
                if next_links[i+1].text != u"后一页":
                    index = int(next_links[i].text)+1
                    break

        return infos, index


    def sync_order(self, shop_id, startTime=None, endTime=None):
        '''
        获取店铺的每笔交易
        '''

        # 时间
        today = datetime.datetime.now()
        # first_day_of_this_month = today.replace(day=1)
        start_date = today - datetime.timedelta(days=30)
        if not startTime:
            startTime = start_date.strftime('%Y-%m-%d')
        if not endTime:
            endTime = today.strftime('%Y-%m-%d')

        # 获取此商户最后一次交易时间
        latest_order_date = datetime.datetime.strptime('2000-01-01 12:00:00', '%Y-%m-%d %H:%M:%S')
        if Order.objects.filter(shop_id=shop_id).count() > 0:
            latest_order_date = Order.objects.filter(shop_id=shop_id).order_by('-order_date')[0].order_date

        shop_orders = []
        page_index = 1
        first = True
        while(page_index > 0):
            orders, page_index = self._sync_order_per_page(shop_id, page_index, latest_order_date, startTime, endTime)
            shop_orders += orders

            # 更新最后交易日期
            if first:
                if orders:
                    s = Shop.objects.get(shop_id=shop_id)
                    s.latest_order_date = orders[0]['order_date']
                    s.save()
                    first = False

        print u'获取商户[ %s ]交易完成，总共更新[ %s ]笔交易。' % (shop_id, len(shop_orders))
        print ''

    def _sync_order_per_page(self, shop_id, page_index, latest_order_date, startTime, endTime):
        '''
        获取每页的交易数据
        '''
        
        req = self.session.get(
            url = self.ORDER_URL + u"%s?page=%s&startTime=%s&endTime=%s" % (shop_id, page_index, startTime, endTime), 
            headers = {"User-Agent": self.USER_AGENT, "Referer": self.SHOP_URL}
        )
        time.sleep(self.SLEEP_TIME)
        doc = pq(req.text)

        # print u'抓取第[ %s ]页交易信息...' % page_index
        infos = []
        is_break = False
        for tr in doc('#example tbody tr'):

            tds = tr.findall('td')
            # 如果没有交易记录则跳过
            if len(tds) <= 1:
                is_break = True
                break

            info = {
                'order_no': tds[0].text,
                'order_date': tds[1].text,
                'card_no': tds[2].text,
                'price': tds[3].text,
                'type': tds[4].text,
                'state': tds[5].text.strip()
            }

            # ==== 保存数据 ====
            order_date = datetime.datetime.strptime(info['order_date'], '%Y-%m-%d %H:%M:%S')
            # 是否到达上次更新点
            if order_date < latest_order_date:
                is_break = True
                break

            try:
                Order.objects.create(
                    shop_id = shop_id,
                    order_no = info['order_no'],
                    order_date = info['order_date'],
                    card_no = info['card_no'],
                    price = info['price'],
                    type = info['type'],
                    pay_type = 1 if info['type'].find(u'微信') > -1 else 2,
                    state = info['state'],
                    rate = self.DICT_SHOP_2_RATE[shop_id] - decimal.Decimal(self.COST),
                    channel_id = self.CHANNEL_ID
                )
            except Exception, e:
                traceback.print_exc()
                continue

            infos.append(info)
            # print info

        print u'第[ %s ]页交易信息抓取完毕。' % page_index
        print ''

        if is_break:
            return infos, -1

        # 判断是否还有下一页
        next_links = doc('.pagination li a')
        index = -1
        for i in range(len(next_links)):
            # 找到当前a标签
            if next_links[i].text == str(page_index):
                # 是否还有下一页
                if next_links[i+1].text != u"后一页":
                    index = int(next_links[i].text)+1
                    break

        return infos, index


if __name__ == "__main__":
    print u"开始搞事情......"
    from www.misc import account
    import sys
    
    # 渠道id
    channel_id = sys.argv[1]
    # 是否初始化
    init = True if sys.argv[2:] == ['init'] else False

    for per in account.ACCOUNTS:
        
        if str(per['CHANNEL_ID']) == channel_id:

            spider = Spider(per['CHANNEL_ID'], per['USERNAME'], per['PASSWORD'], 
                per['COST'], per['DEFAULT_RATE']) 

            if spider.login():
                spider.sync_shop(init)

                for shop in Shop.objects.filter(state=1, channel_id=per['CHANNEL_ID']):
                    print u'---- [ %s - %s ] ----' % (per['USERNAME'], shop.name)
                    if init:
                        spider.sync_order(shop.shop_id, '2017-01-01')
                    else:
                        spider.sync_order(shop.shop_id)














