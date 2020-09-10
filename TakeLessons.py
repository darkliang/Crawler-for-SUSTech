import requests
import re
import time
from retry import retry

delay = 10  # 抢课失败后随机延迟，以毫秒为单位，若不需要则设为0


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
    if p[2] == 'bxqjh':
        r = s.get("http://jwxt.sustech.edu.cn/jsxsd/xsxkkc/bxqjhxkOper?jx0404id=%s&xkzy=&trjf=" % p[1])
    elif p[2] == 'zynknj':
        r = s.get("http://jwxt.sustech.edu.cn/jsxsd/xsxkkc/knjxkOper?jx0404id=%s&xkzy=&trjf=" % p[1])
    elif p[2] == 'kzy':
        r = s.get("http://jwxt.sustech.edu.cn/jsxsd/xsxkkc/fawxkOper?jx0404id=%s&xkzy=&trjf=" % p[1])
    elif p[2] == 'gxk':
        r = s.get("http://jwxt.sustech.edu.cn/jsxsd/xsxkkc/ggxxkxkOper?jx0404id=%s&xkzy=&trjf=" % p[1])
    else:
        print("课程 " + p[0] + " 类别填写错误")

        return False
    result = str(r.content, 'utf-8')
    if result.find("true", 0, len(result)) >= 1:
        print("抢到 " + p[0] + " 啦")
        return True
    if delay <= 0:
        print(result + "继续加油!")
    else:
        print(result + "继续加油!等待%fms" % delay)
        time.sleep(delay / 1000)
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
        s[i].get('http://jwxt.sustech.edu.cn/jsxsd/xsxk/xklc_list?Ves632DSdyV=NEW_XSD_PYGL')
        response = s[i].get('http://jwxt.sustech.edu.cn/jsxsd/xsxk/xklc_list?Ves632DSdyV=NEW_XSD_PYGL')

        print("教务系统启动")
        key = re.findall('href="(.+)" target="blank">进入选课', response.text)
        k = key[0]
        if k:
            s[i].get('http://jwxt.sustech.edu.cn' + k)
        else:
            print("未找到选课入口")
    print("开始抢课")

    rush_all(s, data)
    for i, _ in enumerate(data):
        s[i].close()


if __name__ == '__main__':
    # bxqjh-计划选课,zynknj-专业内跨年级选课,kzy-跨专业选课,gxk-公选课
    data = [{
        'data': {  
            'username': '',
            'password': ''
        },
        'classes': [("计网", "202020211001318", "kzy")]
    }]
    main(data)
