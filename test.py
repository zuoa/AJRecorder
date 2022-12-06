import json
import re
import cv2
from PIL import Image, ImageFont, ImageDraw
import jieba.analyse
from DouyuLive import DouyuLive

if __name__ == '__main__':

    f = open("rooms.json")
    rooms = json.loads(f.read())

    room_config = None
    for room in rooms:
        if room["room_id"] == "7828414":
            room_config = room
            break

    live = DouyuLive(room_config)
    words = ""

    jieba.analyse.set_stop_words('stopwords.txt')
    start_time = "2022-12-03 11:40:00"
    end_time = "2022-12-03 11:55:00"

    live.clip_upload("【煊宝丶】 2022年12月05日 直播回放 弹幕版 <煊里奥历险记~～～>",
                     "/data/AJRecorder/video/source/7828414/7828414_20221205_165206.flv")

    # dm_list = live.danmaku_db.query(start_time, end_time)
    # for dm in dm_list:
    #     words += re.sub("@.*：", " ", dm['content']) + " "
    #
    # keywords = jieba.analyse.extract_tags(words, topK=10)

    # live.cut_file("/Users/yujian/data/AJRecorder/video/source/73965/73965_20221203_110930.flv",
    #               start_time, end_time)
    #
    #
    #
    # start_time = "2022-12-04 22:48:00"
    # end_time = "2022-12-04 22:58:00"
    #
    # live.cut_file("/data/AJRecorder/video/source/73965/73965_20221204_195906.flv",
    #               start_time, end_time)
    #
    # live.cut_file("/data/AJRecorder/video/source/7828414/7828414_20221204_195906.flv",
    #               start_time, end_time)

    #
    # live.upload_file("【阿正时间】" + ",".join(keywords),
    #                  "/Users/yujian/data/AJRecorder/video/source/73965/73965_20221203_110930",
    #                  start_time, end_time)

    # live.uploader.upload("【霸气虚幻哥1991】 2022年11月25日 09时-15时 直播回放 弹幕版 ",
    #                      [
    #                          "/Users/yujian/data/AJRecorder/video/output/73965/20221125094606_20221125101606.ass.mp4",
    #                          "/Users/yujian/data/AJRecorder/video/output/73965/20221125101606_20221125104606.ass.mp4",
    #                          "/Users/yujian/data/AJRecorder/video/output/73965/20221125104606_20221125111606.ass.mp4",
    #                          "/Users/yujian/data/AJRecorder/video/output/73965/20221125111606_20221125114606.ass.mp4",
    #                          "/Users/yujian/data/AJRecorder/video/output/73965/20221125114606_20221125121606.ass.mp4",
    #                          "/Users/yujian/data/AJRecorder/video/output/73965/20221125121606_20221125124606.ass.mp4",
    #                          "/Users/yujian/data/AJRecorder/video/output/73965/20221125124606_20221125131606.ass.mp4",
    #                          "/Users/yujian/data/AJRecorder/video/output/73965/20221125131606_20221125134606.ass.mp4",
    #                          "/Users/yujian/data/AJRecorder/video/output/73965/20221125134606_20221125141606.ass.mp4",
    #                          "/Users/yujian/data/AJRecorder/video/output/73965/20221125141606_20221125144606.ass.mp4",
    #                          "/Users/yujian/data/AJRecorder/video/output/73965/20221125144606_20221125151606.ass.mp4",
    #
    #                       ])
