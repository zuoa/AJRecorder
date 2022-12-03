import os
import datetime
import threading
import cv2
import numpy as np
import re
import jieba.analyse
from DouyuLive import DouyuLive
import aircv as ac

jieba.analyse.set_stop_words('stopwords.txt')
MIN_DELTA = 30

img_start = cv2.imread('./image/start_flag.png')
img_end = cv2.imread('./image/end_flag.png')
img_win = cv2.imread('./image/win_flag.png')
img_cover_flag = cv2.imread('./image/cover_flag.png')


def extract_frames(video_path, dst_folder):
    thread_list = []
    video = cv2.VideoCapture()
    if not video.open(video_path):
        print("can not open the video")
        exit(1)
    fps = video.get(cv2.CAP_PROP_FPS)
    index = 0
    print(f"fps:{fps}")
    start_offset = None
    cover = None
    prepare_cover_times = 0
    while True:
        _, frame = video.read()
        if frame is None:
            break
        second_offset = int(index / fps)
        if index % (fps * 2) == 0:
            frame = cv2.resize(frame, (1920, 1080))
            print(second_offset)

            match_result = ac.find_template(frame, img_start, 0.8, False)
            if match_result:

                if start_offset is None:  # or second_offset - start_offset < MIN_DELTA:
                    start_offset = second_offset

                    rect = match_result['rectangle']
                    cv2.rectangle(frame, (rect[0][0], rect[0][1]), (rect[3][0], rect[3][1]), (0, 0, 30), 2)
                    save_path = "{}/{}_start.png".format(dst_folder, second_offset)
                    cv2.imwrite(save_path, frame)
                    print("=" * 120)
                    print(f"start_offset: {start_offset}")
                    print("=" * 120)

            if start_offset is not None:
                if cover is None or prepare_cover_times < 3:
                    match_result = ac.find_template(frame, img_cover_flag, 0.9, True)
                    if match_result:
                        rect = match_result['rectangle']
                        cv2.rectangle(frame, (rect[0][0], rect[0][1]), (rect[3][0], rect[3][1]), (0, 0, 30), 2)
                        save_path = "{}/{}_{}_cover.png".format(dst_folder, start_offset, second_offset)
                        cv2.imwrite(save_path, frame)
                        cover = save_path
                        print("=" * 120)
                        print(f"cover: {save_path}")
                        print("=" * 120)

                    prepare_cover_times += 1

                match_result = ac.find_template(frame, img_end, 0.8, False)
                if match_result:
                    rect = match_result['rectangle']
                    cv2.rectangle(frame, (rect[0][0], rect[0][1]), (rect[3][0], rect[3][1]), (0, 0, 30), 2)
                    print(start_offset, second_offset)
                    save_path = "{}/{}_{}_end.png".format(dst_folder, start_offset, second_offset)
                    cv2.imwrite(save_path, frame)

                    t = threading.Thread(target=upload, args=(video_path, start_offset, second_offset + 8, cover))
                    t.start()
                    thread_list.append(t)

                    start_offset = None
                    cover = None
                    prepare_cover_times = 0

        index += 1
    video.release()
    # 打印出所提取帧的总数
    print("Totally save {:d} pics".format(index - 1))

    for t in thread_list:
        t.join()


def upload(video_path, start_offset, end_offset, cover=None):
    file = os.path.basename(video_path)
    f_split = file.split("_")
    file_start_time_str = (f_split[1] + f_split[2]).replace(".flv", "")
    file_start_time = datetime.datetime.strptime(file_start_time_str, "%Y%m%d%H%M%S")
    start_time = file_start_time + datetime.timedelta(seconds=start_offset)
    end_time = file_start_time + datetime.timedelta(seconds=end_offset)

    start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

    live = DouyuLive({
        "platform": "douyu",
        "room_id": "110",
        "room_owner_alias": "谢彬DD",
        # "platform": "douyu",
        # "room_id": "73965",
        # "room_owner_alias": "孙正",
        "enable": True,
        "recorder": {
        },
        "clipper": {
            "enable": True,
            "interval": 30,
            "up_threshold_radio": 2,
            "down_threshold_radio": 0.7,
            "start_offset": -15,
            "end_offset": 15
        },
        "processor": {
            "enable": True,
            "overlay_danmaku": True
        },
        "uploader": {
            "bili_tid": 171,
            "tags": [
                "谢彬DD"
            ]
        }
    })
    words = ""

    dm_list = live.danmaku_db.query(start_time_str, end_time_str)
    for dm in dm_list:
        words += re.sub("@.*：", " ", dm['content']) + " "

    keywords = jieba.analyse.extract_tags(words, topK=10)

    live.upload_file(f"【唐门鸭鸭杀】< {start_time_str[5:-3]} > :" + ",".join(keywords),
                     video_path,
                     start_time_str,
                     end_time_str,
                     cover=cover,
                     tags=["丫丫杀", "鸭鸭杀"]
                     )


extract_frames("/Users/yujian/data/AJRecorder/video/source/110/110_20221201_121715.flv", "image/output")
