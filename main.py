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
    print(s)

    # 启动采集
    s.start()
