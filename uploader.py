import os
import datetime
from biliup.plugins.bili_webup import BiliBili, Data

from logger import Logger


class Uploader(object):
    def __init__(self, live, ):
        self.live = live
        self.logger = Logger(__name__).get_logger()

    def upload(self, title, video_files: [], tags=None):
        room_config = self.live.room_config
        video = Data()
        video.title = title
        print(video.title)
        video.desc = self.live.room_id
        # video.source = 'douyu'
        video.copyright = 1
        video.tid = room_config.get('bili_tid', 171)
        generate_tags = ['直播录像',
                         self.live.room_info["cate_name"],
                         self.live.room_info["room_owner"],
                         self.live.room_id]

        generate_tags.extend(room_config.get('bili_tid', []))

        if tags:
            generate_tags.extend(tags)

        if len(generate_tags) > 10:
            generate_tags = generate_tags[:10]

        video.set_tag(generate_tags)
        with BiliBili(video) as bili:
            bili.login("cookies.json", {
                'cookies': {
                    'SESSDATA': self.live.config.get('uploader', {}).get('SESSDATA', ''),
                    'bili_jct': self.live.config.get('uploader', {}).get('bili_jct', ''),
                    'DedeUserID__ckMd5': self.live.config.get('uploader', {}).get('DedeUserID__ckMd5', ''),
                    'DedeUserID': self.live.config.get('uploader', {}).get('DedeUserID', ''),
                    'access_token': self.live.config.get('uploader', {}).get('access_token', '')
                }, 'access_token': self.live.config.get('uploader', {}).get('access_token', '')})
            # bili.login_by_password("username", "password")
            for index, file in enumerate(video_files):
                file_size = os.path.getsize(file)
                if file_size < 10 * 1024 * 1024:
                    continue
                self.logger.info(f"uploading {file}")
                video_part = bili.upload_file(file)  # 上传视频，默认线路AUTO自动选择，线程数量3。
                video_part["title"] = f"{title}- P{index + 1}"
                video.append(video_part)  # 添加已经上传的视频

            print(video)
            if len(video.videos) == 0:
                return

            # video.dtime = dtime  # 设置延后发布（2小时~15天）
            # video.cover = bili.cover_up('/Users/yujian/Downloads/20221109193824.jpg')
            ret = bili.submit()  # 提交视频
            print(ret)

    def upload_file(self, filepath: str, title=None, tags=None):
        if not title:
            file_name = os.path.basename(filepath)
            f_split = file_name.split("_")
            day = datetime.datetime.strptime(f_split[1], "%Y%m%d").strftime("%Y年%m月%d日")
            title = f'【{self.live.room_info["room_owner"]}】<{self.live.room_info["room_name"]}> {day}直播回放'

        file_list = [filepath]
        file_size = os.path.getsize(filepath)
        if file_size < 10 * 1024 * 1024:
            return

        if file_size >= 3 * 1024 * 1024 * 1024:
            file_list = self.processor.cut_file(filepath)

        video = Data()
        video.title = title
        print(video.title)
        video.desc = self.live.room_id
        # video.source = 'douyu'
        video.copyright = 1
        video.tid = 171
        generate_tags = ['直播录像',
                         self.live.room_info["cate_name"],
                         self.live.room_info["room_owner"],
                         self.live.room_id]

        if self.live.tags:
            generate_tags.extend(self.live.tags)

        if tags:
            generate_tags.extend(tags)

        if len(generate_tags) > 10:
            generate_tags = generate_tags[:10]

        video.set_tag(generate_tags)
        with BiliBili(video) as bili:
            bili.login("cookies.json", {
                'cookies': {
                    'SESSDATA': self.live.config.get('uploader', {}).get('SESSDATA', ''),
                    'bili_jct': self.live.config.get('uploader', {}).get('bili_jct', ''),
                    'DedeUserID__ckMd5': self.live.config.get('uploader', {}).get('DedeUserID__ckMd5', ''),
                    'DedeUserID': self.live.config.get('uploader', {}).get('DedeUserID', ''),
                    'access_token': self.live.config.get('uploader', {}).get('access_token', '')
                }, 'access_token': self.live.config.get('uploader', {}).get('access_token', '')})
            # bili.login_by_password("username", "password")
            for index, file in enumerate(file_list):
                video_part = bili.upload_file(file)  # 上传视频，默认线路AUTO自动选择，线程数量3。
                video_part["title"] = f"{title}- P{index + 1}"
                video.append(video_part)  # 添加已经上传的视频

            print(video)
            # video.dtime = dtime  # 设置延后发布（2小时~15天）
            # video.cover = bili.cover_up('/Users/yujian/Downloads/20221109193824.jpg')
            ret = bili.submit()  # 提交视频
            print(ret)
            # if ret["code"] == 0:
            #     for file in file_list:
            #         os.remove(file)


if __name__ == '__main__':
    from DouyuLive import DouyuLive

    Uploader(DouyuLive("73965")).upload("【霸气虚幻哥1991】 2022年11月16日 直播回放 弹幕版 ",
                                        [
                                            "/Users/yujian/data/AJRecorder/video/output/73965/20221116224129_20221116231129.ass.mp4",
                                            "/Users/yujian/data/AJRecorder/video/output/73965/20221116231129_20221116234129.ass.mp4",
                                            "/Users/yujian/data/AJRecorder/video/output/73965/20221116234129_20221117001129.ass.mp4",
                                            "/Users/yujian/data/AJRecorder/video/output/73965/20221117001129_20221117004129.ass.mp4",
                                            "/Users/yujian/data/AJRecorder/video/output/73965/20221117004129_20221117004445.ass.mp4",
                                        ],
                                        tags=["孙正"])
