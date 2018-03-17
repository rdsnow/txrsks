# encoding = utf-8

import requests
from PIL import Image
from bs4 import BeautifulSoup
import sys
import random
from urllib.parse import urlencode

s = requests.session()
join_header = {
    'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)\
         Chrome/58.0.3029.110 Safari/537.36 SE 2.X MetaSr 1.0'
}


def showtxtcode():  # 显示验证码
    url = 'http://txrsks.gov.cn/servlet/com.lzysoft.util.validcode.CodeServlet'
    try:
        req = s.get(url, stream=True)
        with open('vcode.jpg', 'wb')as f:
            for chunk in req.iter_content(chunk_size=1024):
                f.write(chunk)
    except (requests.RequestException, requests.exceptions.ConnectionError) as e:
        print('~~~~(>_<)~~~~ 网络连接错误......\n%s' % e)
        sys.exit()
    with Image.open('vcode.jpg') as img:
        img.show()


def parse_ucen(txt):  # 解析用户中心网页，得到选课的情况
    print(' User imforation '.center(90, '*'))
    soup = BeautifulSoup(txt, "html5lib")
    match = soup.select('.Uleftbg')
    print(match[0].text.strip().split('〖')[0])
    match_course = soup.select('.kecheng')[0].select('tr')
    match_course.pop(0)
    match_course.pop()
    str_course = match_course[0].text.strip()
    sub_tr = '您还没有选课，请先选课。'
    if sub_tr in str_course:
        print(sub_tr)
    else:
        for each in match_course:
            course_name = '在学课程：%s' % each.select('a')[0].text.strip()
            course_link = each.select('a')[0]['href']
            course_id = get_id_from_link(course_link)
            print('%s\t\t\tcourse_id = %s' % (course_name, course_id))


def get_id_from_link(link):  # 从课程超链接的地址中取得课程ID course_id
    course_id = link.split('?')[1].split('&')[0].split('=')[1]
    return course_id


def login_site():  # 登陆网站
    print(' Login site '.center(90, '*'))
    uname = input('请输入您的用户名：')
    pwd = input('请输入您的登陆密码：')
    showtxtcode()
    txtcode = input('请输入看到的验证码：')
    postdata = {'uname': uname, 'pwd': pwd, 'txtCode': txtcode}
    try:
        res = s.post('http://txrsks.gov.cn/login.jsp', data=postdata)
    except (requests.RequestException, requests.exceptions.ConnectionError) as e:
        print(e)
        sys.exit()
    if 'Set-Cookie' in res.headers.keys():  # 注意密码错误也能返回200，这里不检测 status == 200
        print('O(∩_∩)O哈哈~ √ 登陆成功......')
        return True
    else:
        print('~~~~(>_<)~~~~ × 登陆失败，再试试看......')
        return False


def parse_course_page(course_id):  # 分析课程章节的网页，取得每一章的总时长
    front_url = 'http://txrsks.gov.cn/course/course_chapter_list.jsp?course_id=%s'
    url = front_url % course_id
    total_time_list = []
    try:
        res_course = s.get(url)
        soup = BeautifulSoup(res_course.text, 'html5lib')
        match_course = soup.select('.kecheng')[0].select('tr')
        match_course.pop(0)  # 第一行 表头
        match_course.pop(0)  # 第二行 空行
        match_course.pop()  # 空行
        match_course.pop()  # 页码标签行
        for each in match_course:
            course_txt = each.text.strip()
            print(course_txt)
            total_time_list.append(get_total_time_txt(course_txt))
    except (requests.RequestException, requests.exceptions.ConnectionError) as e:
        print('~~~~(>_<)~~~~ 网络连接错误......\n%s' % e)
        sys.exit()
    return total_time_list


def get_total_time_txt(txt):  # 截取html中的x分x秒的文字
    txt = txt[txt.find('秒') + 1:].strip()
    txt = txt[:txt.find('秒') + 1]
    return txt


def get_user_id_from_cookies():  # 取得cookies中的userId
    cookie = s.cookies['DABAO_SHOP_V2']
    cookie = cookie[cookie.find('login_name%3D') + 13:]
    cookie = cookie[:cookie.find('is_super_admin') - 3]
    return cookie


def set_serv_time(course_id, total_time_list):  # 开始秒挂机
    data = {
        'op': 'editMediaPos_exam',
        'totalTime': '',
        'postion': 0,
        'status': 'completed',
        'userId': '',
        'courseId': '',
        'chapterId': 0
    }
    url = 'http://txrsks.gov.cn/servlet/com.lzysoft.action.mediapos.DoAction?'
    chipter = 0
    for each in total_time_list:
        chipter += 1
        minutes = total_time_to_minutes(each)
        data['totalTime'] = minutes_to_chronograph_format(minutes)
        data['postion'] = minutes
        data['chapterID'] = chipter
        data['userId'] = get_user_id_from_cookies()
        data['courseId'] = course_id
        data['chapterId'] = chipter
        try:
            print('......第 %d 章......挂机中........' % chipter + s.get(url + urlencode(data)).text.rstrip('\n'))
        except (requests.RequestException, requests.exceptions.ConnectionError) as e:
            print(e)
    print('以上如果全部显示"OK"，则表示课程已经挂好，可以关闭程序并登陆网站查看')


def total_time_to_minutes(total_time):  # 转换 x分x秒 为总秒数
    total_time_split = total_time.rstrip('秒').split('分')
    minute = int(total_time_split[0])
    second = int(total_time_split[1])
    return minute * 60 + second


def minutes_to_chronograph_format(minutes):  # 转为整数秒数为00:00:00.00格式
    minutes += random.randint(1, 20)
    hour = int(minutes / 3600)
    minutes -= hour * 3600
    minute = minutes // 60
    second = minutes % 60
    return '%02d:%02d:%02d.%02d' % (hour, minute, second, random.randint(0, 99))


def main():
    while login_site() is False:  # 登陆网站，并显示登陆状态
        pass
    while True:
        try:
            res_ucen = s.get('http://txrsks.gov.cn/course/Ucen.jsp')  # 用户中心页面地址
            parse_ucen(res_ucen.text)  # 解析用户中心页面，显示在学课程
        except (requests.RequestException, requests.exceptions.ConnectionError):
            print('~~~~(>_<)~~~~ 网络连接错误......')
            sys.exit()

        print(' Please input course_id '.center(90, '*'))
        print('请输入想要挂机课程ID，输入大于0的数字选择相应的课程，输入非数字退出此程序')
        course_id = input('Please input "course_id" = ')
        if course_id.isnumeric() is False:  # 输入非数字，程序退出
            sys.exit()
        total_time_list = parse_course_page(course_id)
        print(' Set times into server '.center(90, '*'))
        input_char = input("输入'y'开始秒挂课程，输入其他字符退出程序，未报名的课程不要输入'y'，后果未知：(y/n/q)")
        if input_char == 'y':
            set_serv_time(course_id, total_time_list)
        elif input_char == 'q':
            sys.exit()


if __name__ == '__main__':  # 启动程序
    main()
