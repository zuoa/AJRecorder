import os
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

# if __name__ == '__main__':
#     x = get_video_duration("video_src/7828414/7828414_20221108_175406.flv")
#     print(x, int(x / 3600), int(int(x % 3600) / 60), x % 3600 % 60)
