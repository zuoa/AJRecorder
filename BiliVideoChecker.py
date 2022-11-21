import os
import threading
import time

import requests


class BiliVideoChecker(threading.Thread):
    def __init__(self, bvid, video_list):
        super().__init__()

        self.bvid = bvid
        self.video_list = video_list
        self.check_url = "https://api.bilibili.com/x/web-interface/view"
        self.check_interval = 60

        self.session = requests.session()
        self.session.headers.update({
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36 '
        })

    def run(self) -> None:
        while True:
            try:
                resp_check = self.session.get(self.check_url, params={"bvid": self.bvid}).json()
                if resp_check['code'] == 0 and resp_check['data']['state'] == 0:
                    for video in self.video_list:
                        os.remove(video)
                    return
                else:
                    time.sleep(self.check_interval)
            except KeyError:
                pass
