import datetime
import re
import abc
import json
from collections import deque
import requests
from requests.adapters import HTTPAdapter
import jieba.analyse
from logger import Logger
from danmu.DanmuDB import DanmuDB
from clipper import Clipper
from uploader import Uploader

logger = Logger(__name__).get_logger()

jieba.analyse.set_stop_words('stopwords.txt')


class BaseLive(metaclass=abc.ABCMeta):
    def __init__(self, room_config):
        self.room_config = room_config
        self.room_id = room_config["room_id"]
        self._config = {}
        self.room_info = {}
        self.recording_file = None
        self.recent_danmaku_queue = deque(maxlen=8000)
        self.clipping_start_time = None
        self.clipping_end_time = None
        self.danmaku_db = DanmuDB(self.room_id)

        self.session = requests.session()
        self.session.mount('https://', HTTPAdapter(max_retries=3))
        headers = self.config.get('common', {}).get('request_header', {})
        self.session.headers.update(headers)

        self.__last_check_status_time = datetime.datetime.now() - datetime.timedelta(seconds=86400)
        self.__last_check_url_time = datetime.datetime.now() - datetime.timedelta(seconds=86400)
        self.__live_status = False
        self.__live_url = ''
        self.__allowed_check_interval = datetime.timedelta(
            seconds=self.config.get('common', {}).get('check_interval', 60))
        self.refresh_room_info()
        self.uploader = Uploader(self)

    @property
    def config(self):
        if not self._config:
            with open("config.json", "r") as f:
                self._config = json.load(f)

        return self._config

    def refresh_room_info(self):
        self.room_info = self._get_room_info()
        logger.debug(self.generate_log(f"Room info: {self.room_info}"))

    @abc.abstractmethod
    def _get_room_info(self):
        pass

    @abc.abstractmethod
    def _get_live_url(self):
        pass

    @abc.abstractmethod
    def _get_live_status(self) -> bool:
        pass

    @property
    def live_status(self) -> bool:
        if datetime.datetime.now() - self.__last_check_status_time >= self.__allowed_check_interval:
            self.__live_status = self._get_live_status()
            self.__last_check_status_time = datetime.datetime.now()
        return self.__live_status

    @property
    def live_url(self) -> str:
        if datetime.datetime.now() - self.__last_check_url_time >= self.__allowed_check_interval:
            self.__live_url = self._get_live_url()
            self.__last_check_url_time = datetime.datetime.now()
        return self.__live_url

    def select_danmaku_trend(self):
        interval = self.config.get('clipper', {}).get('interval', 30)
        dt_now = datetime.datetime.now()
        dt_series = [dt_now - datetime.timedelta(seconds=interval * i) for i in range(10)]
        danmaku_trend = []
        while True:
            yield danmaku_trend
            danmaku_trend = []
            dt_now = datetime.datetime.now()
            dt_series = [(dt_now - datetime.timedelta(seconds=interval * (i + 1)),
                          dt_now - datetime.timedelta(seconds=interval * i))
                         for i in range(10)]

            danmu_list = self.recent_danmaku_queue.copy()

            for dt in dt_series:
                trend_node = {
                    'dt_start': dt[0].strftime('%Y-%m-%d %H:%M:%S'),
                    'dt_end': dt[1].strftime('%Y-%m-%d %H:%M:%S'),
                    'danmaku_count': 1
                }
                words = ""
                for danmu in danmu_list:
                    # danmu_time = datetime.datetime.strptime(danmu['msg_time'], "%Y-%m-%d %H:%M:%S")
                    if dt[0] < danmu['msg_time'] <= dt[1]:
                        trend_node['danmaku_count'] += 1
                        words += re.sub("@.*：", " ", danmu['content']) + " "

                trend_node["keywords"] = jieba.analyse.extract_tags(words, topK=10)
                danmaku_trend.append(trend_node)

    def push_message(self, title, content):
        push_key = self.config.get('common', {}).get('push_key', '')
        if push_key:
            resp_text_push = requests.post(f'https://sctapi.ftqq.com/{push_key}.send',
                                           {"title": title, "desp": content}).text
            logger.info(resp_text_push)

    def generate_log(self, content):
        return f"{self.room_info.get('room_owner', '')}({self.room_id}):{content}"
