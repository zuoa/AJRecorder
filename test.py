from DouyuLive import DouyuLive

if __name__ == '__main__':
    live = DouyuLive({
        "platform": "douyu",
        "room_id": "73965",
        "room_owner_alias": "孙正",
        "tags": [
            "孙正"
        ],
        "bili_tid": 171,
        "overlay_danmaku": True,
        "active": True
    })

    live.upload_file("【小正学CP】《梦里见》《每天为你唱歌》《小幸运》学的怎么都是自己曾经的样子",
                     "/Users/yujian/data/AJRecorder/video/source/73965/73965_20221122_204546.flv",
                     "2022-11-22 21:55:00",
                     "2022-11-20 23:00:00")
