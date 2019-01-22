import requests, re, json
from fake_useragent import UserAgent


class GetProductInfo:
    __price = False
    __stock = False

    __bsr = False
    __sid = False
    __oid = False

    def __init__(self, asin, seller=None, proxy=None):
        '''初始化类构建所需要参数'''
        # 查询ASIN
        self.__asin = asin
        # 卖家ID
        self.__seller = seller
        # 模拟浏览器
        self.__headers = self.__useragent()
        # 创建代理
        self.__proxies = {'http': proxy, 'https': proxy} if proxy else proxy


    def __send(self,):
        '''发送请求'''
        # 生成查询参数
        query = '/?m=%s' % self.__seller if self.__seller else ''
        # 生成产品链接地址
        url = 'https://www.amazon.com/dp/%s%s'%(self.__asin, query)

        print(url)

        try:
            # 发送请求
            response = requests.get(url, headers=self.__headers, proxies=self.__proxies, timeout=15)
            response.encoding = 'utf-8'
            #
            if response.status_code != 200 or not response.text:

                print('[%s]:请求失败' % self.__asin)
                return False

            if 'Type the characters you see in this image:' in response.text:

                print('[%s]:出现验证码' % self.__asin)

                return False

            return response.text

        except Exception as e:

            print('[%s]:HTTP连接错误!'% self.__asin)
            return False


    def get(self):
        '''获取Asin数据'''

        # 1.发送请求
        htmlStr = self.__send()

        if not htmlStr: return False

        # 2.获取产品页数据
        self.__page1(htmlStr)

        if not self.__bsr:

            print('[%s]:排名获取失败'% self.__asin)
            return False

        if not self.__price:
            print('[%s]:价格获取失败'% self.__asin)
            return False

        if self.__stock:

            return {'bsr': self.__bsr, 'stock': self.__stock, 'price': self.__price}

        if self.__page2() == False:
            print('[%s]:库存获取失败'% self.__asin)
            return False

        return {'bsr': self.__bsr, 'stock': self.__stock, 'price': self.__price}



    def __page1(self,htmlStr):
        '''获取产品页面数据'''

        # 获取页面SessionID
        sid = re.findall(r'id="session-id" name="session-id" value="(.+)?">', htmlStr, re.I)
        if sid: self.__sid = sid[0]

        # 获取页面OfferListingID
        oid = re.findall(r'name=\"offerListingID\" value=\"(.+)\"', htmlStr, re.I)
        if oid: self.__oid = oid[0]

        # 获取BSR排名
        bsr = re.findall(r"#([\d,]+)\sin.*See top 100.*</a>\)", htmlStr, re.I)

        self.__bsr = bsr[0] if bsr else False

        # 获取产品价格
        price = re.findall(r'id=\"priceblock_ourprice.*?>\$([\d.]+)<', htmlStr, re.I)
        self.__price = price[0] if price else False

        # 获取产品库存
        stock = re.findall(r'Only (\d+?) left in stock - order soon.', htmlStr, re.I)

        self.__stock = stock[0] if stock else False

        # 查询卖是否限制购卖数量
        if not stock:

            from lxml import html

            eobj = html.etree.HTML(htmlStr)

            stock = len(eobj.xpath('//select[@id="quantity"]/option/@value'))


            self.__stock = stock if stock < 30 else False
            print(stock)

    def __page2(self):
        '''查询库存数量'''

        # 判断请求参数
        if self.__sid == False and self.__oid == False:

            print('库存查询失败:SessionId和OfferId不能为空')

            return False

        # 请求地址
        url = "https://www.amazon.com/gp/add-to-cart/json/ref=dp_start-bbf_1_glance"
        # 构造请求头
        self.__headers["cookie"] = "session-id=" + self.__sid + "; ubid-main=000-0000000-0000000;"
        # 构造发送数据
        data = {
            'clientName': 'SmartShelf',
            'ASIN': self.__asin,
            'verificationSessionID': self.__sid,
            'offerListingID': self.__oid,
            'quantity': '99999'
        }

        try:
            response = requests.post(url, headers=self.__headers, params=data)

            if response.status_code != 200: return False

            stock = json.loads(response.text)

            if stock.get('isOK'):

                self.__stock = stock.get('cartQuantity')

                return True

            return False

        except Exception as e:

            print(e)
            return False

    def __useragent(self):

        agents = [
            'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
            'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv,2.0.1) Gecko/20100101 Firefox/4.0.1',
            'Mozilla/5.0 (Windows NT 6.1; rv,2.0.1) Gecko/20100101 Firefox/4.0.1',
            'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11',
            'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11',

            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1; 125LA; .NET CLR 2.0.50727; .NET CLR 3.0.04506.648; .NET CLR 3.5.21022)',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0)',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
            'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2)',
            'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 12_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 7.0; SM-G892A Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/60.0.3112.107 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 7.0; SM-G930VC Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/58.0.3029.83 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 6.0.1; SM-G935S Build/MMB29K; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/55.0.2883.91 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 6P Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 6.0; HTC One X10 Build/MRA58K; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/61.0.3163.98 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 6.0; HTC One M9 Build/MRA58K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.3',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/13.2b11866 Mobile/16A366 Safari/605.1.15',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A5370a Safari/604.1',
            'Mozilla/5.0 (iPhone9,4; U; CPU iPhone OS 10_0_1 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Mobile/14A403 Safari/602.1',
            'Mozilla/5.0 (Linux; Android 7.0; Pixel C Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.0.2743.98 Safari/537.36',
            'Mozilla/5.0 (Linux; Android 6.0.1; SGP771 Build/32.2.A.0.253; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.0.2743.98 Safari/537.36',
            'Mozilla/5.0 (Linux; Android 5.0.2; LG-V410/V41020c Build/LRX22G) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/34.0.1847.118 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246',
            'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
            'Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 11_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko'

        ]
        from random import choice
        return {'user-agent': choice(agents)}


if __name__ == '__main__':

    proxy = None

    for n in range(1,20):

        proxy = requests.get('http://198.35.45.110/get?m=mina998').text

        print(proxy)

        data = GetProductInfo('B000RK71LO', 'ATVPDKIKX0DER', proxy).get()

        if data : print(data)

        import time

        time.sleep(3)
