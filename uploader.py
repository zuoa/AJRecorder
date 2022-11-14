import os
import datetime
from biliup.plugins.bili_webup import BiliBili, Data
from processor import Processor


class Uploader(object):
    def __init__(self, live, ):
        self.live = live
        self.processor = Processor(live)

    def upload(self, filepath, title=None, tags=None):
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
    from douyu import DouyuLive

    Uploader(DouyuLive("73965")).upload("video_src/73965/73965_20221114_112900.flv",
                                        title="【正宝TV】20221114 舞力全开 白日舞王", tags=["孙正"])
