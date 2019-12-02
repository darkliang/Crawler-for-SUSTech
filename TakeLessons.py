import requests
import re
import time
from retry import retry

delay = 0  # 抢课失败后随机延迟，以毫秒为单位，若不需要则设为0
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                         ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'}

def rush_all(s, data):
    count = 1
    while len(data) > 0:
        print('\n开始第 %d 次抢课' % count)
        count += 1
        for i, p in enumerate(data):
            print('\n学号：%s' % p['data']['username'])
            for c in p['classes']:
                if rush(s[i], c):
                    p['classes'].remove(c)


def rush(s, p):
    print('正在抢 %s' % p[0])
    r = s.get("http://jwxt.sustech.edu.cn/jsxsd/xsxkkc/fawxkOper?jx0404id=%s&xkzy=&trjf=" % p[1], headers=headers)
    result = str(r.content, 'utf-8')
    if result.find("true", 0, len(result)) >= 1:
        print("抢到 " + p[0] + " 啦")
        return True
    if delay <= 0:
        print(result + "继续加油!")
    else:
        print(result + "继续加油!等待%fs" % (delay/1000))
        time.sleep(delay/1000)
    return False


@retry(delay=0.5)
def main(data):
    s = []
    for i, d in enumerate(data):
        s.append(requests.Session())
        r = s[i].get('https://cas.sustech.edu.cn/cas/login?service=http://jwxt.sustech.edu.cn/jsxsd/')
        data[i]['data']['execution'] = re.findall('on" value="(.+?)"', r.text)[0]
        data[i]['data']['_eventId'] = 'submit'
        data[i]['data']['geolocation'] = ''
        s[i].post('https://cas.sustech.edu.cn/cas/login?service='
                  'http://jwxt.sustech.edu.cn/jsxsd/', data=data[i]['data'])

        print("用户" + data[i]['data']['username'] + " CAS验证成功")
        r = s[i].get('http://jwxt.sustech.edu.cn/jsxsd/xsxk/xklc_list?Ves632DSdyV=NEW_XSD_PYGL')
        print("教务系统启动")
        key = re.findall('href="(.+)" target="blank">进入选课', r.text)
        k = key[0]
        s[i].get('http://jwxt.sustech.edu.cn' + k)

    print("开始抢课")

    rush_all(s, data)
    for i, _ in enumerate(data):
        s[i].close()


if __name__ == '__main__':
    data = [{
        'data': {
            'username': '',
            'password': ''
        },
        'classes': [("Java", '201920201000744')]
    }, {
        'data': {   # 猴哥
            'username': '',
            'password': ''
        },
        'classes': [("PE", '201920201001430')]
    }]
    main(data)

