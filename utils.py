import datetime
from moviepy.editor import VideoFileClip
import traceback
from PIL import ImageFont
from FlvParser import FlvParser


def get_video_duration(filename):
    u"""
    获取视频时长（s:秒）
    """
    file_time = 0
    clip = None
    try:
        clip = VideoFileClip(filename)
        file_time = clip.duration
    except Exception as e:
        traceback.print_exc()
    finally:
        if clip:
            clip.close()
    return file_time


def get_video_real_duration(filename):
    u"""
    获取视频时长（s:秒）
    """
    parser = FlvParser(filename)
    return parser.get_duration()


def get_font_size(font_size, font_path, text):
    u"""
    获取字体大小
    """
    font = ImageFont.truetype(font_path, font_size)
    return font.getsize(text)


def generate_part_title(filename):
    t = filename.split(".")[0]
    start = t.split("_")[0]
    start_time = datetime.datetime.strptime(start, "%Y%m%d%H%M%S")
    return start_time.strftime("%m月%d日 %H时%M分")


if __name__ == '__main__':
    y = get_video_real_duration("/Users/yujian/data/AJRecorder/video/source/7828414/7828414_20221115_162622.flv")
    print(y)
    # x = get_video_duration("/Users/yujian/data/AJRecorder/video/source/7828414/7828414_20221115_161655.flv")
    # print(x)
