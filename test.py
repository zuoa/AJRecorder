from DouyuLive import DouyuLive

if __name__ == '__main__':
    live = DouyuLive({
        "platform": "douyu",
        "room_id": "7828414",
        "room_owner_alias": "煊宝",
        "tags": [
            "煊宝"
        ],
        "bili_tid": 171,
        "overlay_danmaku": True,
        "active": True
    })

    live.upload_file("【煊宝】《量身定做》《一模一样》 你想成为正夫人吗？",
                     "/Users/yujian/data/AJRecorder/video/source/7828414/7828414_20221120_152220.flv",
                     "2022-11-20 18:30:00",
                     "2022-11-20 19:20:00")
