# coding=utf-8
from bs4 import BeautifulSoup
import requests
import time
import pymongo
import random

client = pymongo.MongoClient('localhost', 27017)
ganji = client['ganji']
url_list = ganji['url_list1']
item_info = ganji['item_info1']

headers  = {
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
    'Connection':'keep-alive',
    'Host':'bj.ganji.com',
}

# https://rmccurdy.com/scripts/proxy/good.txt
#国外的不一定可用,部分代理有时效性
proxy_list = [
              'http://58.247.30.222:8080',
              'http://61.135.217.12:80',
              'http://36.97.193.60:8888',
              ]
proxy_ip = random.choice(proxy_list) # 随机获取代理ip
proxies = {'http': proxy_ip}

# spider 1
def get_links_from(channel, pages, who_sells='o'):
    # http://bj.ganji.com/ershoubijibendiannao/o3/
    # o for personal a for merchant
    list_view = '{}{}{}/'.format(channel, str(who_sells), str(pages))
    #wb_data = requests.get(list_view,headers=headers)
    wb_data = requests.get(list_view, headers=headers,proxies=proxies)
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

#get_item_info_from('http://bj.ganji.com/ershoubijibendiannao/2101582357x.htm')
#get_links_from('http://bj.ganji.com/ershoubijibendiannao/',3)
# wrapper > div.leftBox > div.layoutlist > dl:nth-child(5) > dd.feature > div > ul > li > a