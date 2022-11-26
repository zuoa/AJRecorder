import json
import os
import datetime
import time

from biliup.plugins.bili_webup import BiliBili, Data

from BiliVideoChecker import BiliVideoChecker
from utils import generate_part_title
from logger import Logger


class Uploader(object):
    def __init__(self, live, ):
        self.live = live
        self.logger = Logger(__name__).get_logger()

    def upload(self, title, video_files: [], tags=None, cover=None, ):
        self.logger.info(f"try to submit: {title}")
        room_config = self.live.room_config
        video = Data()
        video.title = title
        video.desc = self.live.room_id
        # video.source = 'douyu'
        video.copyright = 1
        video.tid = room_config.get('uploader', {}).get('bili_tid', 171)
        generate_tags = ['直播录像',
                         self.live.room_info["cate_name"],
                         self.live.room_info["room_owner"],
                         self.live.room_id]

        generate_tags.extend(room_config.get('uploader', {}).get('tags', []))

        if tags:
            generate_tags.extend(tags)

        if len(generate_tags) > 10:
            generate_tags = generate_tags[:10]

        video.set_tag(generate_tags)
        with BiliBili(video) as bili:
            bili.login("bili_cookies.json", {})
            # bili.login_by_password("username", "password")
            for file in video_files:
                file_size = os.path.getsize(file)
                if file_size < 10 * 1024 * 1024:
                    continue
                self.logger.info(f"uploading {file}")
                video_part = bili.upload_file(file)  # 上传视频，默认线路AUTO自动选择，线程数量3。
                video_part["title"] = generate_part_title(os.path.basename(file))
                video.append(video_part)  # 添加已经上传的视频

            self.logger.debug(video)
            if len(video.videos) == 0:
                return

            # video.dtime = dtime  # 设置延后发布（2小时~15天）
            if cover:
                video.cover = bili.cover_up(cover)
            submit_times = 0
            while submit_times < 3:
                try:
                    ret = bili.submit()  # 提交视频
                    self.logger.info(ret)
                    self.live.push_message(f"上传成功:{title}", json.dumps(ret))
                    if ret.get('data', {}).get('bvid', None) is not None:
                        checker = BiliVideoChecker(ret.get('data', {}).get('bvid', None), video_files)
                        checker.start()
                        break
                except Exception as e:
                    if e["code"] == 21070:
                        submit_times += 1
                        time.sleep(30)
                    else:
                        break
