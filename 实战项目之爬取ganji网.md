---
title: 实战项目之爬取ganji网
date: 2016-05-17 11:06:04
tags:
---
爬取分类信息网站龙头  ganji网。  

首先呢，来看看结构   
![图1](http://o7b8j5zne.bkt.clouddn.com/ganji%E5%9B%BE1.png) 

我们需要来看看首页那里的所有类目，里面包含20项   
基本上所有的帖子都会被分类在这20个下方，根据时间被分配不同的id，像这样  
http://bj.ganji.com/ershoubijibendiannao/2111373477x.htm  
当然后面加了个x。。。  

- 第一步  
先把这20个类目的地址爬取出来。

```
from bs4 import BeautifulSoup
import requests


start_url = 'http://bj.ganji.com/wu/'
url_host = 'http://bj.ganji.com'

def get_index_url(url):
    # url = start_url
    wb_data = requests.get(url)
    soup = BeautifulSoup(wb_data.text, 'lxml')
    links = soup.select('.fenlei > dt > a')
    for link in links:
        page_url = url_host + link.get('href')
        print(page_url)

get_index_url(start_url)
```   

程序的运行结果是20个链接，  

```
http://bj.ganji.com/jiaju/
http://bj.ganji.com/rirongbaihuo/
http://bj.ganji.com/shouji/
http://bj.ganji.com/shoujihaoma/
http://bj.ganji.com/bangong/
http://bj.ganji.com/nongyongpin/
http://bj.ganji.com/jiadian/
http://bj.ganji.com/ershoubijibendiannao/
http://bj.ganji.com/ruanjiantushu/
http://bj.ganji.com/yingyouyunfu/
http://bj.ganji.com/diannao/
http://bj.ganji.com/xianzhilipin/
http://bj.ganji.com/fushixiaobaxuemao/
http://bj.ganji.com/meironghuazhuang/
http://bj.ganji.com/shuma/
http://bj.ganji.com/laonianyongpin/
http://bj.ganji.com/xuniwupin/
http://bj.ganji.com/qitawupin/
http://bj.ganji.com/ershoufree/
http://bj.ganji.com/wupinjiaohuan/

```   

把这20个链接放入程序中，成为channel\_list。  
这也就是我们的第一个小程序 channel\_extracing.py。  

---  
- 第二步  
从大的分类下获取单个帖子的链接，先来分析下页面结构，   
![图2](http://o7b8j5zne.bkt.clouddn.com/ganji%E5%9B%BE2.png) 

以二手笔记本电脑为例，可以看到后面结构为o＋page，这里o代表的是个人发布的，后面是page。  
那么首先考虑的是构造一个爬虫来抓取links

```
# spider 1
def get_links_from(channel, pages, who_sells='o'):
    # http://bj.ganji.com/ershoubijibendiannao/o3/
    # o for personal a for merchant
    list_view = '{}{}{}/'.format(channel, str(who_sells), str(pages))
    wb_data = requests.get(list_view,headers=headers,proxies=proxies)
    soup = BeautifulSoup(wb_data.text, 'lxml')
    if soup.find('ul', 'pageLink'):
        for link in soup.select('dd.feature div ul li a'):
            item_link = link.get('href')
            if item_link != "javascript:":                
            	url_list.insert_one({'url': item_link})
            	print(item_link)
            # return urls
    else:
        # It's the last page !
        pass
```  
这里注意一下加了一个判断，判断这一页不是最后一页，就是看下方有无pageLink，俗称也就是翻页器类似的，还有就是直接加上了headers部分和proxy部分反爬取。  

函数的结果是urls，并考虑使用mongo数据库来存储这个url\_list。  

接下来就是访问单个的url来抓取里面的数据信息了。  

```
# spider 2
def get_item_info_from(url,data=None):
    wb_data = requests.get(url,headers=headers)
    if wb_data.status_code == 404:
        pass
    else:
        soup = BeautifulSoup(wb_data.text, 'lxml')
        data = {
            'title':soup.title.text.strip(),
            'price':soup.select('.f22.fc-orange.f-type')[0].text.strip(),
            'pub_date':soup.select('.pr-5')[0].text.strip().split(' ')[0],
            'area':list(map(lambda x:x.text,soup.select('ul.det-infor > li:nth-of-type(3) > a'))),
            'cates':list(soup.select('ul.det-infor > li:nth-of-type(1) > span')[0].stripped_strings),
            'url':url
        }
        print(data)
        item_info.insert_one(data)
```  

看图，单个页面我们考虑抓取，标题title 价格price 发布时间pub\_data 交易地点area 类型cates 另外再考虑把url也加入里面。大概先这样咯。  
![图3](http://o7b8j5zne.bkt.clouddn.com/ganji%E5%9B%BE3.png)  

把程序组织一下 组成第二个py程序 page\_parsing.py  
当然详情页抓取的数据我们也放到mongo的数据库中。  

到这里初步小结一下，实现了哪些呢？先是从ganji的首页获取分类，20个分类  
然后在这20个分类下，获取单个帖子的详情页，然后通过详情页去抓取想要的数据。  
爬取的初步流程完成了，接下来就是包装，    
写个主函数，定义下我们抓取多少页的大分类，先url\_list然后item\_info都存入到mongo的数据库中。  
ps 考虑写一个计数的函数观察我们抓取的信息数目。  
  
---  
- 第三步   
主函数的分析   

```
from multiprocessing import Pool  
from page_parsing import get_item_info_from,url_list,item_info,get_links_from  
from channel_extracing import channel_list
```   
也就是前面的两个函数，我们实现了几个功能：
  
channel\_list   
两个方法 get\_item\_info\_from	 get\_links\_from  
两个mongo数据库的collections url\_list item\_info  

另外这里使用多进程来加快抓取的速度	  

```
def get_all_links_from(channel):
    for i in range(1,100):
        get_links_from(channel,i)
```  
注意前面定义的函数我们定义了页面，这里抓取1-99页，当然也许部分分类商品多，99不足，部分分类商品不是很多，我们也已经有判断会pass掉。。  

```
if __name__ == '__main__':
    pool = Pool(processes=6)
    # pool = Pool()
    pool.map(get_all_links_from,channel_list.split())
    pool.close()
    pool.join()
```  
开6个进程进行爬爬爬，先存url，再根据url访问抓取。    

---  
- 第四步    
写上一个计数的函数，这样可以在运行main函数存入数据库时并打印链接的同时，统计已经写了多少数据进去。  


```
import time
from page_parsing import url_list

while True:
    print(url_list.find().count())
    time.sleep(5)
```  

---  
- 最后  
附上项目github地址    [项目地址](https://github.com/zhangdavids/myganji)





