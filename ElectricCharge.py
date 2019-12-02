import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
import matplotlib.pyplot as plt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


class SUSHelper(object):
    __login_uri = "https://cas.sustech.edu.cn/cas/login?service=" \
                  "http://ehall.sustech.edu.cn/dxggyw/sys/sdjfgl/mobile/index.html#/flow"

    # 初始化构造函数，账户和密码
    def __init__(self, username='', password='', room_num='', building_num=''):
        # 账户名
        if not isinstance(username, str):
            raise TypeError('请输入字符串')
        else:
            self.username = username

        if isinstance(password, int):
            self.password = str(password)
        elif isinstance(password, str):
            self.password = password
        else:
            raise TypeError('请输入字符串')

        if isinstance(room_num, int):
            self.room_num = str(room_num)
        elif isinstance(room_num, str):
            self.room_num = room_num
        else:
            raise TypeError('请输入字符串')

        if isinstance(building_num, int):
            self.building_num = str(building_num)
        elif isinstance(building_num, str):
            self.building_num = building_num
        else:
            raise TypeError('请输入字符串')

    # 返回一个登陆成功后的Response
    def get_response_after_login(self):

        # 保持Cookie不变，然后再次访问这个页面
        s = requests.session()
        # 得到一个Response对象，但是此时还没有登录
        r = s.get(self.__login_uri)

        # 得到postdata应该有的lt
        # 这里使用BeautifulSoup对象来解析XML
        # print(r.text)
        soup = BeautifulSoup(r.text, 'html.parser')
        temp = str(soup.find_all(attrs={"name": "execution"})[0])

        exe = re.search(r'value="(.*)\"\/>', temp).group(1)

        params = {
            'username': self.username,
            'password': self.password,
            'execution': exe,
            '_eventId': 'submit',
            'geolocation': ''}
        # 使用构建好的PostData重新登录,以更新Cookie
        room_num = ""
        building_num = ""
        info_uri = "http://ehall.sustech.edu.cn/dxggyw/sys/sdjfgl/modules/mobile/cxyhmtsdxx.do?FJMC={}&LDID={}".format(
            self.room_num, self.building_num)
        margin_uri = "http://ehall.sustech.edu.cn/dxggyw/sys/sdjfgl/paymentController/getFjyl.do?ldid={}&mph={}".format(
            self.building_num, self.room_num)
        s.post(self.__login_uri, data=params)
        info = json.loads(s.get(info_uri).text)["datas"]['cxyhmtsdxx']['rows']
        margin = float(json.loads(s.get(margin_uri).text)
                       ["data"]['data'][0]['dfyl'])/0.717
        return info, margin


if __name__ == "__main__":
    # 已知欣园1栋的building number是01 其他的可以研究API获取
    test = SUSHelper(username='', password='',
                     room_num='', building_num='')
    info, margin = test.get_response_after_login()

    with open("record.txt", "w", encoding='utf-8') as fo:
        content = ''
        for day in info:
            content = "更新日期： " + day['SJTBSJ'] + '\n'
            if day['ZRXFL'] is None:
                content += "\t前日用电：无\n"
            else:
                content += "\t前日用电："+day['ZRXFL']+"度\n"
            content += "\t总计：" + day['FJDQYDZL'] + "度\n\n"
            fo.write(content)

    if margin < 35:
        subject = "电余量不足35度，请及时充值"  # 主题
    else:
        subject = "自动用电量查询"  # 主题

    text = "更新日期： " + info[0]['SJTBSJ'] + '\n'
    if info[0]['ZRXFL'] is None:
        text += "\t前日用电：无\n"
    else:
        text += "\t前日用电：" + info[0]['ZRXFL'] + "度\n"
    text += "\t总计：" + info[0]['FJDQYDZL'] + "度\n"
    text += "剩余电量："+str(margin)+"度\n"

    msg = MIMEMultipart()
    msg.attach(MIMEText(text))
    msg['Subject'] = subject
    msg['From'] = "1111@qq.com"

    # 如果是周日，就发送一周统计图
    if datetime.strptime(info[0]['SJTBSJ'], "%Y-%m-%d %H:%M:%S").weekday() == 0:
        dates = info[0:7]
        # x轴，y轴
        x = [datetime.strptime(d['SJTBSJ'], "%Y-%m-%d %H:%M:%S").date()
             for d in dates]
        y = [float(d['ZRXFL'] if d['ZRXFL'] is not None else 0) for d in dates]

        plt.title("One Week Electricity Consumption")

        # 设置纵轴标签
        plt.ylabel("Energy Used/(kW/h)")

        plt.grid(axis='y')
        # 设置数字标签**
        for a, b in zip(x, y):
            plt.text(a, b, '%.2f' % b, ha='center', va='bottom', fontsize=9)

        # 在当前绘图对象进行绘图（两个参数是x,y轴的数据）
        plt.plot(x, y)
        # 保存图象
        plt.gcf().autofmt_xdate()  # 自动旋转日期标记
        filename = "record-" + \
            datetime.strftime(datetime.now(), "%Y-%m-%d")+".pdf"
        plt.savefig(filename)
        # 添加附件
        part = MIMEApplication(open(filename, 'rb').read())
        part.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(part)

    # 发送邮件部分 替换为自己的邮箱
    s = smtplib.SMTP_SSL("smtp.qq.com", 465)
    s.login('1111@qq.com', '1111')
    s.sendmail("1111@qq.com", "2222@qq.com", msg.as_string())
    s.quit()
