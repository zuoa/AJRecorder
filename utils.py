import os
from moviepy.editor import VideoFileClip
import traceback


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
    print(file_time)
    return file_time




