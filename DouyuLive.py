import threading
import os
import datetime
import sqlite3
import time
from queue import Queue
from logger import Logger

from BaseLive import BaseLive
from processor import Processor
from realurl.douyu import DouYu
from recorder import FlvRecorder
from danmu.douyu import DouyuClient


class DouyuLive(BaseLive):

    def __init__(self, room_config):
        super().__init__(room_config)
        self.logger = Logger(__name__).get_logger()
        self.split_cond = threading.Condition()
        self.split_command_queue = Queue()
        self.upload_command_queue = Queue()

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
        def _danmu_monitor(self):
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
                    self.push_message(f"斗鱼直播间[{self.room_info['room_owner']}]开播通知",
                                      f"房间号：{self.room_id}，房间名：{self.room_info['room_name']}，主播：{self.room_info['room_owner']}，分类：{self.room_info['cate_name']}")

            @client.danmu
            def danmu(message):
                self.recent_danmu_queue.put(message)
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

        def _stream_recorder(self):
            recorder = FlvRecorder(self)
            recorder.run()

        def _clipper(self):
            while True:
                print(self.select_danmaku_trend())
                time.sleep(30)

        def _post_uploader(self):
            while True:
                command = self.upload_command_queue.get()
                if command:
                    self.refresh_room_info()
                    self.uploader.upload(command["title"], command["finished_videos"], cover=command["cover"])

        def _process_timer(self):
            processor = Processor(self)
            processor.process_scheduled()

        return _danmu_monitor, _stream_recorder, _post_uploader, _process_timer, _clipper

    def _run(self):

        danmu_monitor, stream_recorder, post_uploader, process_timer, clipper = self._create_thread_fn()

        danmu_monitor_thread = threading.Thread(target=danmu_monitor, args=(self,))
        danmu_monitor_thread.setDaemon(True)
        danmu_monitor_thread.start()

        stream_recorder_thread = threading.Thread(target=stream_recorder, args=(self,))
        stream_recorder_thread.setDaemon(True)
        stream_recorder_thread.start()

        post_uploader_thread = threading.Thread(target=post_uploader, args=(self,))
        post_uploader_thread.setDaemon(True)
        post_uploader_thread.start()

        process_timer_thread = threading.Thread(target=process_timer, args=(self,))
        process_timer_thread.setDaemon(True)
        process_timer_thread.start()

        clipper_thread = threading.Thread(target=clipper, args=(self,))
        clipper_thread.setDaemon(True)
        clipper_thread.start()

        clipper_thread.join()
        process_timer_thread.join()
        post_uploader_thread.join()
        stream_recorder_thread.join()
        danmu_monitor_thread.join()

    def start(self):
        main_thread = threading.Thread(target=self._run)
        main_thread.start()
        main_thread.join()

    def upload_file(self, title, filepath, start_time_str, end_time_str):
        processor = Processor(self)

        file = os.path.basename(filepath)
        f_split = file.split("_")
        file_start_time_str = (f_split[1] + f_split[2]).replace(".flv", "")
        file_start_time = datetime.datetime.strptime(file_start_time_str, "%Y%m%d%H%M%S")
        start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")

        start_offset = (start_time - file_start_time).seconds
        end_offset = (end_time - file_start_time).seconds
        output_file = processor.process_file(filepath, start_offset, end_offset)
        self.uploader.upload(title, [output_file], tags=["煊正"])
