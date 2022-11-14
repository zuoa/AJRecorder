import time
import re
import threading
import sqlite3
from multiprocessing import Process
from queue import Queue
from logger import Logger

from BaseLive import BaseLive
from realurl.douyu import DouYu
from BaseRecorder import BaseRecorder
from danmu.douyu import DouyuClient


class DouyuLive(BaseLive):

    def __init__(self, room_id, tags=None):
        super().__init__(room_id)
        self.logger = Logger(__name__).get_logger()
        self.tags = tags

    def _get_room_info(self):
        url = 'https://open.douyucdn.cn/api/RoomApi/room/%s' % self.room_id
        resp_json = self.session.get(url).json()
        return {'site_name': '斗鱼',
                'site_domain': 'douyu.com',
                'room_id': self.room_id,
                'room_owner': resp_json['data']['owner_name'],
                'cate_name': resp_json['data']['cate_name'],
                'room_name': resp_json['data']['room_name']}

    def _get_live_url(self):
        return DouYu(self.room_id).get_real_url()

    def _get_live_status(self) -> bool:
        url = 'https://open.douyucdn.cn/api/RoomApi/room/%s' % self.room_id
        resp_json = self.session.get(url).json()
        return resp_json['data']['room_status'] == '1' and resp_json['data']['online'] != '0'

    def _create_thread_fn(self):
        def _danmu_monitor(self, command_queue):
            client = DouyuClient(self.room_id)
            db = sqlite3.connect("danmu.db")
            db_cursor = db.cursor()
            table_name = 'douyu_%s' % self.room_id
            db_cursor.execute("CREATE TABLE IF NOT EXISTS " + table_name +
                              " ('id' INTEGER PRIMARY KEY autoincrement, \
                               'uid' TEXT NOT NULL,'name' TEXT NOT NULL,'badge' TEXT, 'level' INTEGER,\
                               'type' TEXT NOT NULL, 'content' TEXT,'color' TEXT,  'room_id' TEXT,\
                               'room_owner' TEXT, msg_time TIMESTAMP,\
                               'gmt_create' TIMESTAMP default (datetime('now', 'localtime')))", )

            @client.online
            def online(message):
                print("online", message)
                self.__live_status = message["original_msg"]["ss"] == '1'
                if self.__live_status:
                    self.refresh_room_info()

            @client.danmu
            def danmu(message):
                db_cursor.execute("INSERT INTO " + table_name +
                                  "('uid', 'name', 'badge', 'level', 'type', 'content', 'color', 'room_id',\
                                   'room_owner', 'msg_time')\
                                   VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                  (message['uid'], message['nick_name'], message['badge'], message['level'],
                                   message['msg_type'],
                                   message['content'],
                                   message['color'],
                                   message['room_id'], message['room_owner'],
                                   message['msg_time']))
                db.commit()

                if message["uid"] == "22374061":
                    content = message["content"]
                    msg_time = message["msg_time"]
                    if content.startswith("##"):
                        print(content)
                        # command_queue.put(content)

            client.start()

        def _stream_recorder(self, command_queue):
            recorder = BaseRecorder()
            recorder.run(self, command_queue)

        def _post_uploader(self, command_queue):
            while True:
                command = command_queue.get()
                if command:
                    command_type = command["type"]
                    if command_type == "full":
                        self.uploader.upload(command["filepath"])

                time.sleep(5)

        return _danmu_monitor, _stream_recorder, _post_uploader

    def _run(self):
        command_queue = Queue()

        danmu_monitor, stream_recorder, post_uploader = self._create_thread_fn()

        danmu_monitor_thread = threading.Thread(target=danmu_monitor, args=(self, command_queue,))
        danmu_monitor_thread.setDaemon(True)
        danmu_monitor_thread.start()

        stream_recorder_thread = threading.Thread(target=stream_recorder, args=(self, command_queue,))
        stream_recorder_thread.setDaemon(True)
        stream_recorder_thread.start()

        post_uploader_thread = threading.Thread(target=post_uploader, args=(self, command_queue,))
        post_uploader_thread.setDaemon(True)
        post_uploader_thread.start()

        post_uploader_thread.join()
        stream_recorder_thread.join()
        danmu_monitor_thread.join()

    def start(self):
        process = Process(target=self._run)
        process.start()

        # process.join()
