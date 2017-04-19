# -*- coding: utf-8 -*-
import hashlib
import random
import string
import requests
from lxml import etree
from config import wxconfig


ALPHA_LIST = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
              'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd',
              'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x',
              'y', 'z']


def params_filter(sign_parameters):
    """
    对数组排序并除去数组中的空值和签名参数,返回数组和链接串

    :param sign_parameters: 待签名字符串
    """
    sign_array = []
    sign_encode_dict = {}
    for key in sign_parameters:
        s = "%s=%s" % (key, sign_parameters[key])
        sign_array.append(s.encode('utf-8'))
        sign_encode_dict[key] = str(sign_parameters[key]).encode('utf-8')
    sign_array.sort()
    sign_str = "&".join(sign_array)
    return sign_str, sign_array


def wx_build_sign(pre_str):
    """
    生成MD5签名

    :param pre_str: 组装完成的字符串
    """
    pre_str += '&key=%s' % wxconfig.KEY
    return str(hashlib.md5(pre_str).hexdigest()).upper()


def array2xml(pre_str):
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


def get_random_str():
    """生成24位的随机字符串"""
    return string.join(random.sample(ALPHA_LIST, 24)).replace(' ', '')


def create_wx_scan_pay_by_user(order_number, body, total_fee, object_id):
    """
    统一下单——获得生成二维码的code_url
    
    :param order_number: 订单号
    :param body: 商品信息
    :param total_fee: 总价，整数
    :param object_id: 商品的id，扫码支付product_id必传
    """
    url = 'https://api.mch.weixin.qq.com/pay/unifiedorder'
    params = {"out_trade_no": order_number, "body": body, "nonce_str": get_random_str(),
              "trade_type": wxconfig.TYPE, "notify_url": wxconfig.NOTIFY_URL, "total_fee": str(int(total_fee * 100)),
              "product_id": str(object_id), "spbill_create_ip": wxconfig.IP, "appid": wxconfig.APPID,
              "mch_id": wxconfig.MCH_ID}
    sign_str, array = params_filter(params)
    md5_sign = wx_build_sign(sign_str)
    array.append('sign=%s' % md5_sign)
    datas = array2xml(array)
    rsp = requests.post(url, datas)
    root = etree.fromstring(rsp.text)
    if root.findall('return_code')[0].text == 'SUCCESS':
        if root.findall('result_code')[0].text == 'SUCCESS':
            return root.findall('code_url')[0].text
    else:
        return None