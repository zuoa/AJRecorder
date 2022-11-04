import datetime
import abc
import requests
from requests.adapters import HTTPAdapter
from logger import Logger


class BaseLive(metaclass=abc.ABCMeta):
    def __init__(self, config: dict, room_id):
        self.logger = Logger(__name__).get_logger()
        default_headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36 '
        }
        self.headers = {**default_headers, **config.get('root', {}).get('request_header', {})}
        self.session = requests.session()
        self.session.mount('https://', HTTPAdapter(max_retries=3))
        self.room_id = room_id
        self.config = config
        self.__last_check_time = datetime.datetime.now() + datetime.timedelta(
            seconds=-config.get('root', {}).get('check_interval', 60))
        self.__live_status = False
        self.__live_url = ''
        self.__allowed_check_interval = datetime.timedelta(seconds=config.get('root', {}).get('check_interval', 60))
        self.room_info = self._get_room_info()
        self.logger.debug(f"Room info: {self.room_info}")

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
            self.logger.debug("允许检查")
            print("允许检查")
            self.__live_status = self._get_live_status()
        else:
            self.logger.debug("间隔不足，使用过去状态")
            print("间隔不足，使用过去状态")
        return self.__live_status

    @property
    def live_url(self) -> str:
        if datetime.datetime.now() - self.__last_check_time >= self.__allowed_check_interval:
            self.logger.debug("允许检查")
            self.__live_url = self._get_live_url()
        else:
            self.logger.debug("间隔不足，使用过去状态")
        return self.__live_url
