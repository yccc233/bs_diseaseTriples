import http.client
import hashlib
import urllib
from urllib import parse
import random
import json
import time

appid = '20210324000740657'  # 填写你的appid
secretKey = '13pXNyQraMMH2I2H_bTM'  # 填写你的密钥


def trans_zh_en(zh):
    time.sleep(1)
    httpClient = None
    url = 'http://api.fanyi.baidu.com/api/trans/vip/translate'
    fromLang = 'zh'  # 原文语种
    toLang = 'en'  # 译文语种
    salt = random.randint(32768, 65536)
    q = zh
    # domai = 'medicine'
    sign = appid + str(q) + str(salt) + secretKey
    sign = hashlib.md5(sign.encode()).hexdigest()
    # exit(9)
    myurl = url + '?appid=' + appid + '&q=' + urllib.parse.quote(
        q) + '&from=' + fromLang + '&to=' + toLang + '&salt=' + str(salt) + '&sign=' + sign

    try:
        httpClient = http.client.HTTPConnection('api.fanyi.baidu.com')
        httpClient.request('GET', myurl)

        # response是HTTPResponse对象
        response = httpClient.getresponse()
        result_all = response.read().decode("utf-8")
        result = json.loads(result_all)
        return result['trans_result'][0]['dst']
    except Exception as e:
        print(e)
        return ''
    finally:
        if httpClient:
            httpClient.close()


if __name__ == '__main__':
    diseases_zh = []
    with open('../data/phen.txt','r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line not in diseases_zh:
                diseases_zh.append(line)
    counts = len(diseases_zh)
    diseases_en = []
    for i in range(0,counts):
        print('\r%.2f%%'%(i*100/counts),end='')
        diseases_en.append(trans_zh_en(diseases_zh[i]))
    with open('../data/phen_en.txt', 'w+') as f:
        for disease in diseases_en:
            f.write(disease)
            f.write('\n')