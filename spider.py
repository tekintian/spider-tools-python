import requests
from requests.adapters import HTTPAdapter

import chardet
import re
import os
import sys
import io
import gzip
# 引入rand_ua.py里面的定义的变量ua_list
from rand_ua import get_rand_ua

# spider采集工具类
# @author tekintian@gmail.com


class Spider(object):
    # 定义构造方法
    def __init__(self, url, re_title, re_list, re_content, re_intro='', save_dir='article/', timeout=60, max_retry=3):
        # 设置属性
        self.def_charset = "utf-8"
        self.timeout = timeout
        self.max_retry = max_retry
        self.url = url
        self.re_title = re_title
        self.re_list = re_list
        self.re_content = re_content
        self.re_intro = re_intro
        # 验证save_dir是否非绝对路径,如果非绝对路径加上当前目录
        if not save_dir.startswith('/'):
            save_dir = os.getcwd()+'/' + save_dir
        # 验证存放目录 save_dir 是否存在
        if not os.path.isdir(save_dir) and not os.path.isfile(save_dir):
            os.mkdir(save_dir)
        self.save_dir = save_dir

    # 输出对象的字符串(追踪对象属性信息变化)
    def __str__(self):  # __str__(self)不可以添加参数(形参)
        return "url: %s save_dir: %s def_charset: %s " % (self.url, self.save_dir, self.def_charset)

    # 在控制台打印日志
    def show_log(self, msg):
        sys.stdout.write(msg)
        sys.stdout.flush()
    # 请求网络数据, 兼容不同网页编码,支持gzip, 解决了返回乱码问题
    # @author tekintian@gmail.com

    def http_req(self, url):
        req = requests.Session()
        req.mount('http://', HTTPAdapter(max_retries=self.max_retry))
        req.mount('https://', HTTPAdapter(max_retries=self.max_retry))

        # try:
        # r = req.get('http://www.google.com.hk', timeout=5)
        # return r.text
        # except requests.exceptions.RequestException as e:
        # print(e)
        # print(time.strftime('%Y-%m-%d %H:%M:%S'))
        # 自定义请求header
        req.headers = {'User-Agent': get_rand_ua(),
                       'Accept-Encoding': 'gzip, deflate', 'Accept': '*/*', 'Connection': 'keep-alive'}
        # 设置最大重试次数
        i = 0
        while i < self.max_retry:
            try:
                # 注意这里的请求方式, 如果Request没有传递data数据,则默认为get请求,如果有 data=xxx 则为POST请求
                r = req.get(url=url, timeout=self.timeout)
                data = r.content  # content获取的是byte, 如果是text获取的是unicode str
                # res = request.urlopen(req)
                # data = res.read()
                # 自动检测内容编码 解决返回数据编码问题导致的乱码
                chd = chardet.detect(data)
                charset = chd['encoding']
                if charset != '' and charset != None:  # 如果检测到编码, 将数据编码设置为检测到的编码,忽略其他编码
                    data = data.decode(charset, 'ignore')
                elif charset == None:  # 如果charset为 None 可能是被压缩了,解压后再编码
                    data = gzip.decompress(data).decode(
                        self.def_charset, 'ignore')
                else:
                    data = data.decode(self.def_charset, 'ignore')
                # 请求成功,返回
                if r.status_code == 200:
                    return str(data)
                else:
                    i = i+1
                    self.show_log("URL: %s 第 %d 次网络请求异常, status_code: %d " %
                                  (url, i, r.status_code))
            except requests.exceptions.RequestException as ex:
                i += 1
                self.show_log("URL: %s 第 %d 次网络请求异常: %s " %
                              (url, i, ex.strerror))

    # 获取内容文本

    def get_content_txt(self, durl):
        data = self.http_req(durl)
        if data == None:
            self.show_log("get_content_txt durl: %s 在重试 %d 次仍然异常!, data: %s " %
                          (durl, self.max_retry, data))
            return
        # 获取标题
        matche = re.search(self.re_title, data)
        if matche:
            title = '## '+matche.groupdict().get('title')+'\r\n\r\n'
        else:
            title = '## Spider'+'\r\n\r\n'
        # 正则获取内容
        matches = re.search(self.re_content, data)
        # 获取指定的匹配组
        content = matches.groupdict().get('content')
        # 将html的br换行替换为 \r\n
        content = re.sub(r'<br(|.*?)>', "\r\n", content)
        # 将2个以上的连续换行符替换为1个
        # content = re.sub(r'([\r\n]{1,})', "\r\n", content)
        # 删除2个以上的空格和所有的非img标签
        content = re.sub(r'([&nbsp;]{2,})|<([^img].*?)>', "", content)

        return title+content

    # base_url解析

    def get_base_url(self, uri):
        if uri.startswith('/'):  # 如果是相对跟目录的绝对路径
            matche_u = re.search(r'(https?://(.*?))/', self.url)
            if matche_u:
                self.base_url = matche_u[1]
        elif not uri.startswith('http', 0, 4):  # 相对于当前页面的url
            self.base_url = self.url[0:self.url.rindex('/')+1]
        else:
            self.base_url = ''
        return self.base_url

    # 开始采集
    def start(self):
        print('开始采集')
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding=self.def_charset)
        data = self.http_req(self.url)
        # 正则获取标题
        matche = re.search(self.re_title, data)
        if matche:
            title = matche.groupdict().get('title')
        else:
            title = 'spider'
        filename = self.save_dir+title+'.txt'  # 文件名定义

        intro = ''  # 描述 默认为空
        if self.re_intro != '':
            matche = re.search(self.re_intro, data)
            if matche:
                intro = matche.groupdict().get('intro')
                # 去除所有html标签
                intro = re.sub(r'<[\s\S]+?>', '', intro)

        # 获取urls
        matches = re.findall(self.re_list, data)
        le = len(matches)
        if le > 0:
            uri0 = matches[0]
            base_url = self.get_base_url(uri0)
            # 覆盖写入
            file = open(filename, 'w', encoding=self.def_charset)
            file.write('# '+title+'\r\n'+intro)  # 写入小说名称
            file.close()
            # 以追加读写模式打开
            file = open(filename, 'a+', encoding=self.def_charset)
            for index in range(le):
                sys.stdout.write('\r正在采集第: '+str(index+1)+' 页, 总:'+str(le))
                sys.stdout.flush()
                # 获取列表中的url链接地址,
                duri = matches[index]
                # 获取指定的匹配组
                durl = base_url+duri
                txt = self.get_content_txt(durl)
                file.write(txt)

            file.flush()
            file.close()
            print('\r\n采集完成')
        else:
            txt = self.get_content_txt(self.url)
            if txt != '':
                file = open(filename, 'w', encoding=self.def_charset)
                file.write(txt)
                file.flush()
                file.close()
                print('采集完成')
            else:
                print('未匹配到数据')
