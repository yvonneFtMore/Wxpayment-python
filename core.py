# -*- coding: utf-8 -*-
import hashlib
import json
import random
import string
import requests
import time
from lxml import etree
from config import wxconfig


ALPHA_LIST = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
              'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd',
              'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x',
              'y', 'z']


class WechatUtils(object):

    def __init__(self):
        self.access_token = 0
        self.at_valid_time =0
        self.jsapi_ticket = 0
        self.jsapi_valid_time = 0

    def get_web_snsapi_base(self, code):
        """获取用户openid，使用snsapi_base方式"""
        url = 'https://api.weixin.qq.com/sns/oauth2/access_token?appid=%s&secret=%s&c' \
              'ode=%s&grant_type=authorization_code' % (wxconfig.APPID, wxconfig.APPSECRET, code)
        data = requests.get(url)
        return json.loads(data.text)['openid']

    def get_access_token(self, refresh=False):
        """获取access_token"""
        now = int(time.time())
        if self.access_token != 0 and now < self.at_valid_time and not refresh:
            return self.access_token
        else:
            url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential' + \
                  '&appid=%s&secret=%s' % (wxconfig.APPID, wxconfig.APPSECRET)
            try:
                req = requests.get(url)
                parsed = json.loads(req.text)
                if 'access_token' in parsed:
                    self.access_token = parsed['access_token']
                    self.at_valid_time = now + 7000
            except:
                return False
            return self.access_token

    def get_jsapi_ticket(self):
        """使用jsapi的config中签名需要jsapi_ticket"""
        now = int(time.time())
        if self.jsapi_ticket!=0 and now < self.jsapi_valid_time:
            return self.jsapi_ticket
        url = 'https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token=%s&type=jsapi' % self.get_access_token()
        try:
            req = requests.get(url)
            parsed = json.loads(req.text)
            if 'ticket' in parsed and parsed['errcode'] == 0:
                self.jsapi_ticket = parsed['ticket']
                self.jsapi_valid_time = now + 7000
        except:
            return False
        return self.jsapi_ticket

    def jsapi_config_sign(self, url):
        """生成使用jsapi的config中的signature"""
        ret = {
            'nonceStr': self.get_random_str(),
            'jsapi_ticket': self.get_jsapi_ticket(),
            'timestamp': int(time.time()),
            'url': url
        }
        sign_value = '&'.join(['%s=%s' % (key.lower(), ret[key]) for key in sorted(ret)])
        ret['signature'] = hashlib.sha1(sign_value).hexdigest()
        return ret

    def params_filter(self, sign_parameters):
        """
        对数组排序并除去数组中的空值和签名参数,返回数组和链接串
    
        :param sign_parameters: 待签名字符串
        """
        sign_array = []
        sign_encode_dict = {}
        for key in sign_parameters:
            if len(sign_parameters[key]) != 0:
                s = "%s=%s" % (key, sign_parameters[key])
                sign_array.append(s.encode('utf-8'))
                sign_encode_dict[key] = str(sign_parameters[key]).encode('utf-8')
        sign_array.sort()
        sign_str = "&".join(sign_array)
        return sign_str, sign_array

    def wx_build_sign(self, pre_str):
        """
        生成MD5签名
    
        :param pre_str: 组装完成的字符串
        """
        pre_str += '&key=%s' % wxconfig.KEY
        return str(hashlib.md5(pre_str).hexdigest()).upper()

    def array2xml(self, pre_str):
        """
        list转xml
        
        :param pre_str: 排好序的待转换参数
        """
        xml_param = '<xml>'
        for key in pre_str:
            info = key.split('=')
            xml_param += '<' + info[0] + '>' + info[1] + '</' + info[0] + '>'
        xml_param += '</xml>'
        return xml_param

    def get_random_str(self):
        """生成24位的随机字符串"""
        return string.join(random.sample(ALPHA_LIST, 24)).replace(' ', '')

    def choose_wx_pay(self, prepay_id):
        """生成使用chooseWXPay中的paySign"""
        data = {'package': 'prepay_id=%s' % prepay_id,
                'nonceStr': self.get_random_str(),
                'signType': 'MD5',
                'timeStamp': '%s' % int(time.time()),
                'appId': wxconfig.APPID}
        sign_value = '&'.join(['%s=%s' % (key, data[key]) for key in sorted(data)])
        data['signature'] = self.wx_build_sign(sign_value)
        return data


class Payment(object):

    def create_wx_scan_pay_by_user(self, order_number, body, total_fee, object_id):
        """
        统一下单——获得生成二维码的code_url
        
        :param order_number: 订单号
        :param body: 商品信息
        :param total_fee: 总价，整数
        :param object_id: 商品的id，扫码支付product_id必传
        """
        wechat = WechatUtils()
        url = 'https://api.mch.weixin.qq.com/pay/unifiedorder'
        params = {"out_trade_no": order_number, "body": body, "nonce_str": wechat.get_random_str(),
                  "trade_type": wxconfig.TYPE, "notify_url": wxconfig.NOTIFY_URL, "total_fee": str(int(total_fee * 100)),
                  "product_id": str(object_id), "spbill_create_ip": wxconfig.IP, "appid": wxconfig.APPID,
                  "mch_id": wxconfig.MCH_ID}
        sign_str, array = wechat.params_filter(params)
        md5_sign = wechat.wx_build_sign(sign_str)
        array.append('sign=%s' % md5_sign)
        datas = wechat.array2xml(array)
        rsp = requests.post(url, datas)
        root = etree.fromstring(rsp.text)
        if root.findall('return_code')[0].text == 'SUCCESS':
            if root.findall('result_code')[0].text == 'SUCCESS':
                return root.findall('code_url')[0].text
        else:
            return None

    def create_wx_gongzhong_pay_by_user(self, order_number, body, total_fee, object_id, openid, ip):
        """
        公众号支付交易接口
    
        :param order_number: 订单号
        :param body: 交易内容——购买商品：xxxxx
        :param total_fee: 收取的金额
        :param object_id: 商品ID
        :param openid: 用户微信OPENID
        :param ip: 用户端IP
        """
        wechat = WechatUtils()
        url = 'https://api.mch.weixin.qq.com/pay/unifiedorder'
        params = {"out_trade_no": order_number, "body": body, "nonce_str": wechat.get_random_str(),
                  "trade_type": wxconfig.MOBILE_TYPE, "notify_url": wxconfig.NOTIFY_URL,
                  "total_fee": str(int(total_fee * 100)), "product_id": str(object_id), "spbill_create_ip": '%s' % ip,
                  "appid": wxconfig.APPID, "mch_id": wxconfig.MCH_ID, "openid": openid}
        sign_str, array = wechat.params_filter(params)
        md5_sign = wechat.wx_build_sign(sign_str)
        array.append('sign=%s' % md5_sign)
        datas = wechat.array2xml(array)
        rsp = requests.post(url, datas)
        root = etree.fromstring(rsp.text)
        if root.findall('return_code')[0].text == 'SUCCESS':
            if root.findall('result_code')[0].text == 'SUCCESS':
                return wechat.choose_wx_pay(root.findall('prepay_id')[0].text)
        else:
            return