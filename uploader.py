import json
import os
import datetime
from biliup.plugins.bili_webup import BiliBili, Data
from utils import generate_part_title
from logger import Logger


class Uploader(object):
    def __init__(self, live, ):
        self.live = live
        self.logger = Logger(__name__).get_logger()

    def upload(self, title, video_files: [], tags=None):
        self.logger.info(f"try to submit: {title}")
        room_config = self.live.room_config
        video = Data()
        video.title = title
        video.desc = self.live.room_id
        # video.source = 'douyu'
        video.copyright = 1
        video.tid = room_config.get('bili_tid', 171)
        generate_tags = ['直播录像',
                         self.live.room_info["cate_name"],
                         self.live.room_info["room_owner"],
                         self.live.room_id]

        generate_tags.extend(room_config.get('tags', []))

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
            # video.cover = bili.cover_up('/Users/yujian/Downloads/20221109193824.jpg')
            ret = bili.submit()  # 提交视频

            self.live.push_message(f"上传完成:{title}", json.dumps(ret))
            self.logger.info(ret)

if __name__ == '__main__':
    from DouyuLive import DouyuLive

    room_config = {
        "platform": "douyu",
        "room_id": "73965",
        "room_owner_alias": "孙正",
        "tags": [
            "孙正"
        ],
        "bili_tid": 171,
        "overlay_danmaku": True,
        "active": True
    }
    Uploader(DouyuLive(room_config)).upload("【霸气虚幻哥1991】 2022年11月16日 直播回放 弹幕版 ",
                                            [
                                                "/Users/yujian/data/AJRecorder/video/output/73965/20221116224129_20221116231129.ass.mp4",
                                                "/Users/yujian/data/AJRecorder/video/output/73965/20221116231129_20221116234129.ass.mp4",
                                                "/Users/yujian/data/AJRecorder/video/output/73965/20221116234129_20221117001129.ass.mp4",
                                                "/Users/yujian/data/AJRecorder/video/output/73965/20221117001129_20221117004129.ass.mp4",
                                                "/Users/yujian/data/AJRecorder/video/output/73965/20221117004129_20221117004445.ass.mp4",
                                            ],
                                            tags=["孙正"])
