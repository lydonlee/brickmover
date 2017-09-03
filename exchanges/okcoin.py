#encoding: utf-8

import json
import httplib
import datetime
import cookielib
import urllib, urllib2
import random
import logging
import os
import lxml.html
import lxml.etree 
from selenium import webdriver
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pickle
import config
from info import *

driver = webdriver.Chrome('/home/logan/anaconda3/lib/python3.6/site-packages/chromedriver')
_logger = logging.getLogger('exchanges')

class OKCoinBtcDepositParser():
    def __init__(self):
        #self.btc_deposit_address_path = '//div[@class="fincoinaddress-1"]/span'
        self.money_balance_id = "bannerUserCnyBalance"
        self.btc_balance_id = "bannerUserBtcBalance"
        self.btc_deposit_address = "3AL482CnTVWhv6pew1MfcxtTXVABwi4c8T"
        self.money_balance = 0.0
        self.btc_balance = 0.0
        self.soup = None
    '''
    def parse(self, html):
        tree = lxml.html.document_fromstring(html)
        #self.btc_deposit_address = tree.xpath(self.btc_deposit_address_path)[0].text
        self.money_balance = float(tree.get_element_by_id(self.money_balance_id).value)
        self.btc_balance = float(tree.get_element_by_id(self.btc_balance_id).value)
        print "self.money_balance",self.money_balance
        print "btc_balance",self.btc_balance
    '''
class OKCoinExchange:
    Name = 'okcoin'
    session_period = 10
    HOST = 'www.okcoin.cn'
    BASE_URL = 'https://' + HOST

    def __init__(self, cfg):
        self._config = cfg
        self.can_withdraw_stock_to_address = False
        self.stock_withdraw_fee = 0.0001
        self.trade_fee = self._config['trade_fee']
        self._last_logged_time = None
        self.cookie_file = os.path.join(config.configuration['data_path'], 'okcoin.cookies')
        self.cookieJar = cookielib.MozillaCookieJar(self.cookie_file)
        # user provided username and password
        self.username = self._config['user_name']
        self.password = self._config['password']
        self.trade_password = self._config['trade_password']
        # set up opener to handle cookies, redirects etc
        self.opener = urllib2.build_opener(
            urllib2.HTTPRedirectHandler(),
            urllib2.HTTPHandler(debuglevel=0),
            urllib2.HTTPSHandler(debuglevel=0),
            urllib2.HTTPCookieProcessor(self.cookieJar)
        )
        # pretend we're a web browser and not a python script
        #self.opener.addheaders = [('User-agent', 
        #    ('Mozilla/4.0 (compatible; MSIE 10.0; '
        #    'Windows NT 5.2; .NET CLR 1.1.4322)'))
        #]
        self.opener.addheaders = [('User-agent', 
            ('Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:55.0) Gecko/20100101 Firefox/55.0'))
        ]

    def _make_post_url(self, action):
        rnd = int(random.random() * 100)
        return OKCoinExchange.BASE_URL + action + '?random=' + str(rnd)

    def _send_sms_code(self, type, withdraw_amount, withdraw_btc_addr, symbol):
        '''
        type 的解释：
        1: BTC/LTC提现
        2: 设置提现地址
        3: 人民币提现
        '''
        self.login()
        url = self._make_post_url('/account/sendMsgCode.do')
        params = urllib.urlencode({
            'type': type, 
            'withdrawAmount': withdraw_amount, 
            'withdrawBtcAddr': withdraw_btc_addr, 
            'symbol':symbol
        })
        response = self.opener.open(url, params)
        response.close()
     
    def login(self):
        if self._last_logged_time and ((datetime.datetime.now() - self._last_logged_time).total_seconds() < OKCoinExchange.session_period * 60):
            print "already login in!"
            return

        self._last_logged_time = datetime.datetime.now()       
        driver.get(self.BASE_URL)

        try:
            element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "indexLoginName"))
            )
        finally:
            pass
        pickle.dump(driver.get_cookies() , open(self.cookie_file,"wb"))

        e_username = driver.find_element_by_id("indexLoginName")
        e_password = driver.find_element_by_id("indexLoginPwd")
         

        e_username.clear()
        e_password.clear()

        e_username.send_keys(self.username)
        e_password.send_keys(self.password)

        driver.find_element_by_id("indexLoginSubmit").click()
        pickle.dump(driver.get_cookies() , open(self.cookie_file,"wb"))
        driver.close()
    '''
    def login(self):
        if self._last_logged_time and ((datetime.datetime.now() - self._last_logged_time).total_seconds() < OKCoinExchange.session_period * 60):
            return
        base_url = 'https://' + OKCoinExchange.HOST
        self._last_logged_time = datetime.datetime.now()
        print(OKCoinExchange.BASE_URL)
        # open the front page of the website to set and save initial cookies
        response = self.opener.open(OKCoinExchange.BASE_URL)
        self.cookieJar.save()
        response.close()

        login_data = urllib.urlencode({
            'loginName' : self.username,
            'password' : self.password
        })
        login_action = '/login/index.do'
        login_url = self._make_post_url(login_action)
        print "login_url=",login_url
        print "login_data=",login_data
        #https://www.okcoin.cn/user/login/index.do?random=81
        response = self.opener.open(login_url, login_data)
        self.cookieJar.save()
        #print self.cookieJar._cookies
        print "response=",response.read()
        response.close()
    '''
    
    def request_ticker(self):
        url = 'https://www.okcoin.cn/api/ticker.do'
        response = urllib2.urlopen(url, timeout=10)
        ticker_data = json.loads(response.read())['ticker']
        ticker = Ticker(float(ticker_data['buy']), float(ticker_data['sell']), float(ticker_data['last']))
        return ticker

    '''
    def request_info(self):
        _logger.info(u'准备开始请求 okcoin.com 帐号信息')
        ticker = self.request_ticker()
        self.login()
        response = self.opener.open('https://www.okcoin.cn/spot/accountBalance.do')
        parser = OKCoinBtcDepositParser()
        html = response.read()

        parser.parse(html)     
        btc_deposit_address = parser.btc_deposit_address
        response.close()
        #withdraw_btc_addr = '17Ar3q9Bkfz7i6RhTJcobgnYw6gNVfE4JE'
        #withdraw_amount = '0.1'
        #type = 1
        #symbol='btc'
        #self._send_sms_code(type, withdraw_amount, withdraw_btc_addr, symbol)
        return AccountInfo(OKCoinExchange.Name, ticker, self.trade_fee, parser.money_balance, parser.btc_balance, btc_deposit_address)
    '''
    def loadcookie(self,driver):
        for cookie in pickle.load(open(self.cookie_file, "rb")):
            driver.add_cookie(cookie)
            print "load cookie :", cookie
    def test_cookie(self):
        self.loadcookie(driver)
        driver.get("https://www.okcoin.cn/trade/btc.do")
        temp1 = driver.find_element_by_id('bannerUserCnyBalance').text
        temp2 = driver.find_element_by_id('bannerUserBtcBalance').text
        print "bannerUserCnyBalance=",temp1
        print "bannerUserBtcBalance=",temp2

    def request_info(self):
        _logger.info(u'准备开始请求 okcoin.com 帐号信息')
        ticker = self.request_ticker()

        self.login()
        
        self.loadcookie(driver)
        driver.get("https://www.okcoin.cn/trade/btc.do")
        try:
            element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "bannerUserCnyBalance"))
            )
        finally:
            pass

        temp1 = driver.find_element_by_id('bannerUserCnyBalance').text
        temp2 = driver.find_element_by_id('bannerUserBtcBalance').text
        print "bannerUserCnyBalance=",temp1
        print "bannerUserBtcBalance=",temp2

        #money_balance = float(driver.find_element_by_id("bannerUserCnyBalance").text)
        #btc_balance = float(driver.find_element_by_id("bannerUserBtcBalance").text)
        btc_deposit_address = "3AL482CnTVWhv6pew1MfcxtTXVABwi4c8T"
        
        #print "money_balance:",money_balance
        #print "btc_balance:",btc_balance
        #return AccountInfo(OKCoinExchange.Name, ticker, self.trade_fee, money_balance, btc_balance, btc_deposit_address)

    def withdraw_stock(self, address, amount):
        trade_data = urllib.urlencode({
            'withdrawAddr': '',
            'withdrawAmount': amount,
            'tradePwd': self.trade_password,
            'validateCode': '',
            'symbol': 0,
        })
        action = '/account/withdrawBtc.do'
        url = self._make_post_url(action)
        response = self.opener.open(url, trade_data)
        response.close()

    def buy(self, stock_qty, price):
        self.buysell(self, stock_qty, price,0)

    def sell(self, stock_qty, price):
        self.buysell(self, stock_qty, price,1)

    def buysell(self, stock_qty, price,tradetype):
        loadcookie(driver)
        driver.get("https://www.okcoin.cn/trade/btc.do")
        if (tradetype == 0):
            driver.find_element_by_link_text('Buy BTC').click()
            
        else:
            driver.find_element_by_link_text('Sell BTC').click()

        amount = driver.find_element_by_id("tradeAmount")
        cnyprice = driver.find_element_by_id("tradeCnyPrice")
        submit = driver.find_element_by_id("btnA")

        amount.clear()
        cnyprice.clear()

        amount.send_keys(stock_qty)
        cnyprice.send_keys(price)
        submit.click()
    '''
    def sell(self, stock_qty, price):
        trade_data = urllib.urlencode({
            'tradeAmount': stock_qty,
            'tradeCnyPrice': price,
            'tradePwd': "",
            #self.trade_password,
            'symbol': 0,
            'limited':0,
            #tradeAmount:tradeAmount,tradeCnyPrice:tradeCnyPrice,tradePwd:tradePwd,symbol:symbol,limited:limited
        })
        action = '/trade/sellBtcSubmit.do'
        #/trade/sellBtcSubmit.do?random=
        url = self._make_post_url(action)
        print "sell url=",url
        print "trade_data=",trade_data
        response = self.opener.open(url, trade_data)
        print response.read()
        response.close()
        '''