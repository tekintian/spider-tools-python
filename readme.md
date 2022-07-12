# Python spider数据采集工具类

面向对象的python spider数据采集工具模块封装, 采用高效灵活的正则封装和匹配数据, 简洁,高效,快速!

支持列表采集;
详情页采集;
支持一次性采集列表中的所有页面内容到同一个txt文件;
支持任意网页编码;
支持gzip压缩后的网页;
彻底解决中文乱码问题;
支持随机UA,防拉黑功能等;


## 小说采集示例

~~~py
from spider import Spider

if __name__ == "__main__":
    # 根据要采集的站点来配置相应的正则
    url = 'https://www.yruan.com/article/41479.html'  # 要采集的URL 地址,支持单页地址或者列表地址
    re_title = '<h1>(?P<title>[\s\S]+?)<'  # 标题正则
    re_content = '<div id="content">(?P<content>[\s\S]+?)</div>'  # 内容URL正则
    re_list = '<dd><a href="(.*?)"'  # 列表URL地址正则
    re_intro = '<div id="intro">(?P<intro>[\s\S]+?)</div>'  # 简介正则
    save_dir = 'article/'  # 小说保存目录, 可以是相对当前目录,也可以是绝对路径,最后带 /

    # 实例化一个Spider对象
    s = Spider(url=url, re_title=re_title, re_list=re_list,
               re_content=re_content, re_intro=re_intro, save_dir=save_dir)
    # 启动采集
    s.start()
~~~

要采集其他内容,只需要替换上面的相关网址,正则即可~



## Spider面向过程封装

~~~py
# spider数据采集工具类 函数模式

工程中使用还是使用面向对象的class封装方式,  这个函数式仅做学习面向对象和面向过程的学习对比参考

~~~py
from urllib import request
import chardet
import re
import os
import sys
import io
import gzip
# 引入rand_ua.py里面的定义的变量ua_list
from rand_ua import get_rand_ua

# spider数据采集 函数模式
# 请求数据
def http_req(url):
    # 自定义请求header
    headers = {'User-Agent': get_rand_ua(), 'Referer': ''}
    # 注意这里的请求方式, 如果Request没有传递data数据,则默认为get请求,如果有 data=xxx 则为POST请求
    req = request.Request(url=url, headers=headers)
    res = request.urlopen(req)
    data = res.read()
    # 自动检测内容编码 解决返回数据编码问题导致的乱码
    chd = chardet.detect(data)
    charset = chd['encoding']
    if charset != '' and charset != None:  # 如果检测到编码, 将数据编码设置为检测到的编码,忽略其他编码
        data = data.decode(charset, 'ignore')
    elif charset == None:  # 如果charset为 None 可能是被压缩了,解压后再编码
        data = gzip.decompress(data).decode("utf-8", 'ignore')
    else:
        data = data.decode("utf-8", 'ignore')

    return data

# 获取内容文本
def get_content_txt(url, re_title, re_content):
    data = http_req(url)
    # 获取标题
    matche = re.search(re_title, data)
    if matche:
        title = '## '+matche.groupdict().get('title')+'\r\n\r\n'
    else:
        title = '## Spider'+'\r\n\r\n'
    # 正则获取内容
    matches = re.search(re_content, data)
    # 获取指定的匹配组
    content = matches.groupdict().get('content')
    # 将html的br换行替换为 \r\n
    content = re.sub(r'<br(|.*?)>', "\r\n", content)
    # 将2个以上的连续换行符替换为1个
    # content = re.sub(r'([\r\n]{1,})', "\r\n", content)
    # 删除2个以上的空格和所有的非img标签
    content = re.sub(r'([&nbsp;]{2,})|<([^img].*?)>', "", content)

    return title+content

# 获取待采集的列表url
def spider_start(url, re_title, re_list, re_content, re_intro='', save_dir='article/'):
    data = http_req(url)
    # 正则获取标题
    matche = re.search(re_title, data)
    if matche:
        title = matche.groupdict().get('title')
    else:
        title = '小说'
    # 验证save_dir是否非绝对路径,如果非绝对路径加上当前目录
    if not save_dir.startswith('/'):
        save_dir = os.getcwd()+'/'+save_dir
    # 验证存放目录 save_dir 是否存在
    if not os.path.isdir(save_dir) and not os.path.isfile(save_dir):
        os.mkdir(save_dir)
    filename = save_dir+title+'.txt'  # 文件名定义

    intro = ''  # 描述 默认为空
    if re_intro != '':
        matche = re.search(re_intro, data)
        if matche:
            intro = matche.groupdict().get('intro')
            # 去除所有html标签
            intro = re.sub(r'<[\s\S]+?>', '', intro)

    # 获取urls
    matches = re.findall(re_list, data)
    le = len(matches)
    if le > 0:
        uri0 = matches[0]  # 取第一个uri来分析base_url
        if uri0.startswith('/'):  # 如果是相对跟目录的绝对路径
            matche_u = re.search(r'(https?://(.*?))/', url)
            if matche_u:
                base_url = matche_u[1]
        elif not uri0.startswith('http', 0, 4):  # 相对于当前页面的url
            base_url = url[0:url.rindex('/')+1]
        else:  # url为完整的url, 不需要加base_url
            base_url = ''
        # 覆盖写入
        file = open(filename, 'w', encoding='utf-8')
        file.write('# '+title+'\r\n'+intro)  # 写入小说名称
        file.close()
        # 以追加读写模式打开
        file = open(filename, 'a+', encoding='utf-8')
        for index in range(le):
            sys.stdout.write('\r正在采集第: '+str(index)+' 章, 总:'+str(le))
            sys.stdout.flush()
            # 获取列表中的url链接地址,
            uri = matches[index]
            # 获取指定的匹配组
            url = base_url+uri
            txt = get_content_txt(url, re_title, re_content)
            file.write(txt)

        file.flush()
        file.close()
        print('\r\n采集完成')
    else:
        txt = get_content_txt(url, re_title, re_content)
        if txt != '':
            file = open(filename, 'w', encoding='utf-8')
            file.write(txt)
            file.flush()
            file.close()
            print('采集完成')
        else:
            print('未匹配到数据')

print('开始采集')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')
# change for actual site
# 根据要采集的站点来配置相应的正则
re_title = '<h1>(?P<title>[\s\S]+?)<'  # 标题正则
re_intro = '<div id="intro">(?P<intro>[\s\S]+?)</div>'  # 简介正则
re_content = '<div id="content">(?P<content>[\s\S]+?)</div>'  # 内容URL正则
re_list = '<dd><a href="(.*?)"'  # 列表URL地址正则

spider_start('https://www.yruan.com/article/41479.html',
             re_title, re_list, re_content, re_intro)

~~~
~~~
