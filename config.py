# -*- coding: utf-8 -*-

LOCALHOST = 'http://www.xxx.com'

class wxconfig:
    """
    微信支付——统一下单

    :param KEY: API接口密钥，以数字和字母组成的32位字符
    :param APPID: 商户的appid
    :param MCH_ID: 商户号
    :param HOST: 组装链接头
    :param NOTIFY_URL: 异步回调通知
    :param IP: 请求的IP地址
    """

    HOST = 'weixin://wxpay/bizpayurl?'

    KEY = ''

    APPID = ''

    APPSECRET = ''

    MCH_ID = ''

    TYPE = 'NATIVE'

    MOBILE_TYPE = 'JSAPI'

    NOTIFY_URL = LOCALHOST + '/xxxxx/'

    IP = ''