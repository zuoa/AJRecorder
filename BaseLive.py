import datetime
import abc
import json
import requests
from requests.adapters import HTTPAdapter
from logger import Logger
from uploader import Uploader

logger = Logger(__name__).get_logger()


class BaseLive(metaclass=abc.ABCMeta):
    _config = {}
    room_info = {}

    def __init__(self, room_id):
        self.room_id = room_id

        self.session = requests.session()
        self.session.mount('https://', HTTPAdapter(max_retries=3))
        headers = self.config.get('common', {}).get('request_header', {})
        self.session.headers.update(headers)

        self.__last_check_time = datetime.datetime.now() + datetime.timedelta(
            seconds=-self.config.get('common', {}).get('check_interval', 60))
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
        logger.debug(f"Room info: {self.room_info}")

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
        if datetime.datetime.now() - self.__last_check_time >= self.__allowed_check_interval:
            self.__live_status = self._get_live_status()
        return self.__live_status

    @property
    def live_url(self) -> str:
        if datetime.datetime.now() - self.__last_check_time >= self.__allowed_check_interval:
            logger.info("允许检查")
            self.__live_url = self._get_live_url()
        else:
            logger.info("间隔不足，使用过去状态")
        return self.__live_url
