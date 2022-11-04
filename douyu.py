import time
import threading
from BaseLive import BaseLive
from realurl.douyu import DouYu
from multiprocessing import Process

from logger import Logger
from BaseRecorder import BaseRecorder


class DouyuLive(BaseLive):
    def __init__(self, room_id):
        super().__init__({}, room_id)
        self.logger = Logger(__name__).get_logger()

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
            while True:
                print('心跳')
                time.sleep(30)

        def _stream_recorder(self):
            while True:
                print('录制')
                time.sleep(10)

        return _danmu_monitor, _stream_recorder

    def _run(self):
        recorder = BaseRecorder()
        recorder_thread = threading.Thread(target=recorder.run, args=(self,))
        recorder_thread.setDaemon(True)
        recorder_thread.start()

        recorder_thread.join()

    def start(self):
        process = Process(target=self._run)
        process.start()

        # process.join()
