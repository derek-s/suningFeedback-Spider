# -*- coding: utf-8 -*-
"""苏宁易购差评抓取并提供分析
@module:suningNegSpider
@runtime: Python 2.x
2017-10-16
"""

import json
import time
import re
import urllib2
import csv
import codecs
import datetime
from bs4 import BeautifulSoup

# 构造请求头
REQUEST_HEADERS = {
    "Accept-Language":
    "en,zh-CN;q=0.8,zh;q=0.6,ja;q=0.4,zh-TW;q=0.2,es;q=0.2",
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
    "Accept":
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection":
    "keep-alive"
}
commodityrep = []
commoditylinks = []


def suningindexs():
    """搜索商品返回页数量抓取
    Args: None"""
    keyword = urllib2.quote(raw_input("抓取关键词: "))
    print keyword

    testurl = """https://search.suning.com/{serach}/&sc=0&ct=1&st=0"""
    si_request = urllib2.Request(
        testurl.format(serach=keyword), headers=REQUEST_HEADERS)
    si_pagesources = urllib2.urlopen(si_request).read()
    si_pagesoup = BeautifulSoup(si_pagesources, "html.parser")
    # 获取页码数量
    rep = r"\d+"
    try:
        si_pagenumberem = re.findall(rep,
                                     si_pagesoup.find(
                                         'span',
                                         class_="TV-page-move").get_text())
    except:
        try:
            si_pagenumberem = re.findall(rep,
                                         si_pagesoup.find(
                                             'span',
                                             class_="page-more").get_text())
        except:
            try:
                pagens = si_pagesoup.find(
                    'div',
                    class_="little-page").find('span').get_text().replace(
                        '\n', '').split('/')[1]
                si_pagenumberem = []
                si_pagenumberem.append(pagens)
            except:
                si_pagenumberem = ['1']
    print '页码合计: ', si_pagenumberem[0]
    # 将所有商品搜索结果页传入suninglinks进行商品页抓取
    for pagen in range(0, int(si_pagenumberem[0])):
        si_pagen = str(pagen)
        print '抓取第 ', pagen + 1, ' 页'
        url = """https://search.suning.com/{serach}/&sc=0&ct=1&st=0&cp={number}"""
        suninglinks(url.format(serach=keyword, number=si_pagen))
        # print url.format(number=pagen)
    # suninglinks('https://search.suning.com/%e8%81%94%e6%83%b3/&sc=0&ct=1&st=0&cp=0')


def suninglinks(pageurl):
    """商品详情页面url抓取
    Args:
    pageurl: 商品列表页url 字符串"""
    sl_request = urllib2.Request(pageurl, headers=REQUEST_HEADERS)
    sl_pagesources = urllib2.urlopen(sl_request).read()
    sl_pagesoup = BeautifulSoup(sl_pagesources, "html.parser")
    sl_links = sl_pagesoup.find_all('a', class_="sellPoint")
    for x in sl_links:
        """
        if x.get('buyproduct') is None:
            commodityrep.append(x.get('href'))
        else:
            commodityrep.append(x.get('buyproduct'))
        """
        commodityrep.append(x.get('href'))


if __name__ == '__main__':
    suningindexs()
    commoditylinks = list(set(commodityrep))
    commoditylinks.sort(key=commodityrep.index)
    print '商品详情页信息抓取完成'
    strtime = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    with open(strtime + '.csv', 'wb') as csvfile:
        csvfile.write(codecs.BOM_UTF8)
        badwrite = csv.writer(csvfile, dialect='excel')
        badwrite.writerow([
            '用户名', '用户等级', '用户差评ID', '用户差评内容', '用户差评时间', '评价有用数', '客服回复名称',
            '客服回复内容', '客服回复时间', '时间间隔'
        ])
        badurl = """https://review.suning.com/ajax/review_lists/general-000000000{id}-{shop}-bad-1-default-20-----reviewList.htm?callback=reviewList"""
        for x in commoditylinks:
            request = urllib2.Request(
                badurl.format(
                    id=x.split('/')[4].split('.')[0], shop=x.split('/')[3]),
                headers=REQUEST_HEADERS)
            # request = urllib2.Request(badurl.format(id='169465400', shop='0000000000', headers=REQUEST_HEADERS))
            jsondata = urllib2.urlopen(request).read().split('reviewList(')
            jsontest = json.loads(jsondata[1][:-1])
            if 'commodityReviews' in jsontest.keys():
                if len(jsontest['commodityReviews']) == 0:
                    print '该条暂无差评'
                    continue
                else:
                    for badp in jsontest['commodityReviews']:
                        print '用户名: ', badp['userInfo']['nickName']
                        print '用户等级: ', badp['userInfo']['levelName']
                        print '用户差评ID: ', badp['commodityReviewId']
                        print '用户差评内容: ', badp['content']
                        print '用户差评时间: ', badp['publishTime']
                        usefulurl = """https://review.suning.com/ajax/useful_count/{commid}-usefulCnt.htm"""
                        usefulreq = urllib2.Request(
                            usefulurl.format(commid=badp['commodityReviewId']),
                            headers=REQUEST_HEADERS)
                        usefuldata = urllib2.urlopen(usefulreq).read().split(
                            'usefulCnt(')[1][:-1]
                        usefuljson = json.loads(usefuldata)
                        print '评价有用数: ', str(usefuljson[
                            'reviewUsefuAndReplylList'][0]['usefulCount'])
                        replyurl = """https://review.suning.com/ajax/reply_list/{commid}--1-replylist.htm"""
                        replyreq = urllib2.Request(
                            replyurl.format(commid=badp['commodityReviewId']),
                            headers=REQUEST_HEADERS)
                        replydata = urllib2.urlopen(replyreq).read().split(
                            'replylist(')[1][:-1]
                        replyjson = json.loads(replydata)
                        if len(replyjson['replyList']) == 0:
                            print '暂无客服回复信息'
                            badwrite.writerow([
                                str(badp['userInfo']['nickName'].encode(
                                    'utf-8')),
                                str(badp['userInfo']['levelName'].encode(
                                    'utf-8')),
                                str(badp['commodityReviewId']),
                                str(badp['content'].encode('utf-8')),
                                str(badp['publishTime'].encode('utf-8')),
                                str(usefuljson['reviewUsefuAndReplylList'][0][
                                    'usefulCount']), '暂无', '暂无', '暂无', '暂无'
                            ])
                        else:
                            print '客服回复名称: ', replyjson['replyList'][0][
                                'replyList'][0]['replyUserNickName']
                            print '客服回复内容: ', replyjson['replyList'][0][
                                'replyList'][0]['replyContent']
                            print '客服回复时间: ', replyjson['replyList'][0][
                                'replyList'][0]['replyTime']
                            replydate = replyjson['replyList'][0]['replyList'][
                                0]['replyTime']
                            replydatelist = replydate.replace(
                                ' ', ',').replace('-', ',').replace(
                                    ':', ',').split(',')
                            replyyear = int(replydatelist[0])
                            if replydatelist[1][0:1] == '0':
                                replymonth = int(replydatelist[1][1:2])
                            else:
                                replymonth = int(replydatelist[1])
                            if replydatelist[2][0:1] == '0':
                                replydays = int(replydatelist[2][1:2])
                            else:
                                replydays = int(replydatelist[2])
                            if replydatelist[3][0:1] == '0':
                                replyhours = int(replydatelist[3][1:2])
                            else:
                                replyhours = int(replydatelist[3])
                            if replydatelist[4][0:1] == '0':
                                replymins = int(replydatelist[4][1:2])
                            else:
                                replymins = int(replydatelist[4])
                            if replydatelist[5][0:1] == '0':
                                replysocs = int(replydatelist[5][1:2])
                            else:
                                replysocs = int(replydatelist[5])
                            usrcontdate = badp['publishTime']
                            usrcontdatelist = badp['publishTime'].replace(
                                ' ', ',').replace('-', ',').replace(
                                    ':', ',').split(',')
                            usrcontyears = int(usrcontdatelist[0])
                            if usrcontdatelist[1][0:1] == '0':
                                usrcontmonth = int(usrcontdatelist[1][1:2])
                            else:
                                usrcontmonth = int(usrcontdatelist[1])
                            if usrcontdatelist[2][0:1] == '0':
                                usrcontdays = int(usrcontdatelist[2][1:2])
                            else:
                                usrcontdays = int(usrcontdatelist[2])
                            if usrcontdatelist[3][0:1] == '0':
                                usrconthours = int(usrcontdatelist[3][1:2])
                            else:
                                usrconthours = int(usrcontdatelist[3])
                            if usrcontdatelist[4][0:1] == '0':
                                usrcontmins = int(usrcontdatelist[4][1:2])
                            else:
                                usrcontmins = int(usrcontdatelist[4])
                            if usrcontdatelist[5][0:1] == '0':
                                usrcontsocs = int(usrcontdatelist[5][1:2])
                            else:
                                usrcontsocs = int(usrcontdatelist[5])
                            relpyd = datetime.datetime(replyyear, replymonth,
                                                       replydays, replyhours,
                                                       replymins, replysocs)
                            usrcontd = datetime.datetime(
                                usrcontyears, usrcontmonth, usrcontdays,
                                usrconthours, usrcontmins, usrcontsocs)
                            print '客服回复与用户评价间隔时间: %.2f' % (
                                datetime.timedelta.total_seconds(
                                    relpyd - usrcontd) / 3600)
                            # print type(badp['userInfo']['nickName'].encode('utf-8'))
                            badwrite.writerow([
                                str(badp['userInfo']['nickName'].encode(
                                    'utf-8')),
                                str(badp['userInfo']['levelName'].encode(
                                    'utf-8')),
                                str(badp['commodityReviewId']),
                                str(badp['content'].encode('utf-8')),
                                str(badp['publishTime'].encode('utf-8')),
                                str(usefuljson['reviewUsefuAndReplylList'][0][
                                    'usefulCount']),
                                str(replyjson['replyList'][0]['replyList'][0][
                                    'replyUserNickName'].encode('utf-8')),
                                str(replyjson['replyList'][0]['replyList'][0][
                                    'replyContent'].encode('utf-8')),
                                str(replyjson['replyList'][0]['replyList'][0][
                                    'replyTime'].encode('utf-8')),
                                str('%.2f' % (datetime.timedelta.total_seconds(
                                    relpyd - usrcontd) / 3600))
                            ])
                            time.sleep(3)
            else:
                print 'key不存在'
                continue
    print '抓取完成'