import time
import threading
from BaseLive import BaseLive
from realurl.douyu import DouYu
from multiprocessing import Process

from logger import Logger
from BaseRecorder import BaseRecorder
from danmu.douyu import DouyuClient
from queue import Queue


class DouyuLive(BaseLive):
    def __init__(self, room_id):
        super().__init__({}, room_id)
        self.logger = Logger(__name__).get_logger()
        self.command_queue = Queue()

    def _get_room_info(self):
        url = 'https://open.douyucdn.cn/api/RoomApi/room/%s' % self.room_id
        resp_json = self.session.get(url).json()
        return {'site_name': '斗鱼',
                'site_domain': 'douyu.com',
                'room_id': self.room_id,
                'room_owner': resp_json['data']['owner_name']}

    def _get_live_url(self):
        return DouYu(self.room_id).get_real_url()

    def _get_live_status(self) -> bool:
        url = 'https://open.douyucdn.cn/api/RoomApi/room/%s' % self.room_id
        resp_json = self.session.get(url).json()
        return resp_json['data']['room_status'] == '1'

    def _create_thread_fn(self):
        def _danmu_monitor(self):
            client = DouyuClient(self.room_id)

            @client.danmu
            def danmu(message):
                if message["uid"] == "22374061":
                    content = message["content"]
                    msg_time = message["msg_time"]
                    if content.startswith("#cut"):
                        content_split = content.split(" ")
                        print(content)
                        print(msg_time)
                        self.command_queue.put(content_split)

            client.start()

        def _stream_recorder(self):
            recorder = BaseRecorder()
            recorder.run(self)
        def _post_processor(self):
            recorder = BaseRecorder()
            recorder.run(self)

        return _danmu_monitor, _stream_recorder, _post_processor

    def _run(self):
        danmu_monitor, stream_recorder, post_processor = self._create_thread_fn()

        danmu_monitor_thread = threading.Thread(target=danmu_monitor, args=(self,))
        danmu_monitor_thread.setDaemon(True)
        danmu_monitor_thread.start()

        stream_recorder_thread = threading.Thread(target=stream_recorder, args=(self,))
        stream_recorder_thread.setDaemon(True)
        stream_recorder_thread.start()

        stream_recorder_thread.join()
        danmu_monitor_thread.join()

    def start(self):
        process = Process(target=self._run)
        process.start()

        # process.join()
