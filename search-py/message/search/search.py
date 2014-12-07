from __future__ import absolute_import
from message import MessageRecv

#from database.models import EnterpriseUser, Channel, Program
#from database import models

import requests
#import datetime
#from pytz import timezone

#from datetime import timedelta
#from bs4 import BeautifulSoup
#from django.utils import timezone
#from django.http import HttpResponse
import json
#import iso8601
from SocialTV import settings
import logging
#from common.task import BaseTask, TaskQueue

from bs4 import BeautifulSoup
import re

class SearchRecv(MessageRecv):
    @classmethod
    def get_message_type(cls):
        return 'search'

    def parse(self, data):
        self.require_fields(data, 'keywords', 'filter', 'startIndex', 'requestCount', 'inDays', 'sortWay')
        self.data = data
        return True

    def handle_impl(self):
        req = requests.post(settings.SEARCH_URL+"/stvsearch/_search", data=json.dumps(self.data))
        logging.info(json.dumps(self.data))
        logging.info(req.text)
        return self.reply_result(result = req.json())

class LoadExternalRecv(MessageRecv):
    @classmethod
    def get_message_type(cls):
        return 'load-external'

    def parse(self, data):
        self.require_fields(data, 'url')
        self.url = data['url']
        return True

    def handle_impl(self):
        req =  requests.get(self.url)
        if req.status_code== 200:
            html_doc =req.text #.encode('utf8', 'replace')
            soup = BeautifulSoup(html_doc)
            result = []

            if soup.find(id='pl-load-more-destination'):
                for each_li in soup.find(id='pl-load-more-destination').findChildren(recursive=False):
                    item          = {}
                    item['title'] = each_li['data-title']
                    item['id']    = each_li['data-video-id']
                    item['thumb']   = "http://i.ytimg.com/vi/"+ each_li['data-video-id'] +"/hqdefault.jpg"
                    item['url'] = "https://www.youtube.com/watch?v="+ each_li['data-video-id']
                    if each_li.find('div',{'class':'timestamp'}):
                        item['length'] =   each_li.find('div',{'class':'timestamp'}).get_text()
                        result.append(item)
            elif soup.find('meta',{'itemprop':'videoId'}):
                item          = {}
                item['title'] = soup.find('meta',{'itemprop':'name'})['content']
                item['id']    = soup.find('meta',{'itemprop':'videoId'})['content']
                length = soup.find('meta',{'itemprop':'duration'})['content']
                item['thumb']   = "http://i.ytimg.com/vi/"+ item['id'] +"/hqdefault.jpg"
                item['url'] = "https://www.youtube.com/watch?v="+ item['id']
                match = re.match('^P(\d*)M(\d*)S$', length, re.IGNORECASE)
                if match:
                    item['length'] = str(match.group(1))+':'+str(match.group(2))
                result.append(item)

            return self.reply_result(result = result)
        else:
            return self.reply_result(result ={'error_msg' :'External video URL can not be accessed.'})
