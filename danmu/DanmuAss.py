import os
import datetime
import random

from utils import get_font_size

DANMU_VIEWPORT_WIDTH = 560
DANMU_VIEWPORT_HEIGHT = 420
DANMU_VIEWPORT_OFFSET_Y = 10
DANMU_TIME = 12000
FONT_FAMILY = "Source Han Sans CN"
FONT_SIZE = 20
DANMU_LINE_HEIGHT = FONT_SIZE + 2


def get_danmu_width(text):
    # return get_font_size(FONT_SIZE, FONT_FAMILY, text)[0]
    return len(text) * FONT_SIZE


def offset_millisecond_to_datetime(millisecond):
    millis = millisecond % 1000
    second_total = int(millisecond / 1000)
    hours = int(second_total / 3600)
    minutes = int(second_total % 3600 / 60)
    seconds = second_total % 3600 % 60
    return f"{hours}:{minutes:0>2d}:{seconds:0>2d}.{millis}"


class Ass:
    def __init__(self, danmu_list, video_start_time, ass_filepath):
        self.danmu_list = danmu_list
        self.video_start_time = video_start_time
        if not os.path.exists(os.path.dirname(ass_filepath)):
            os.makedirs(os.path.dirname(ass_filepath))
        self.fp = open(ass_filepath, "w")

        self._header = f"""[Script Info]
Title: Made By zuoa
ScriptType: v4.00+
Collisions: Normal
PlayResX: {DANMU_VIEWPORT_WIDTH}
PlayResY: {DANMU_VIEWPORT_HEIGHT}
Timer: 10.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: R2L,{FONT_FAMILY},{FONT_SIZE},&H10FFFFFF,&H99FFFFFF,&H99000000,&H99000000,1,0,0,0,100,100,0,0,1,1,0,2,20,20,2,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def flush(self):
        self.fp.write(self._header)
        tracks = [None for _ in range(int((DANMU_VIEWPORT_HEIGHT - DANMU_VIEWPORT_OFFSET_Y * 2) / DANMU_LINE_HEIGHT))]
        for index, dm in enumerate(self.danmu_list):
            danmu = AssDanmu(dm["msg_time"], dm["content"], dm["color"], self.video_start_time)
            i = 0
            while i < len(tracks):
                if tracks[i] is None or danmu.compare(tracks[i]):
                    tracks[i] = danmu
                    danmu.y = (i + 1) * DANMU_LINE_HEIGHT + DANMU_VIEWPORT_OFFSET_Y

                    self.fp.write(
                        rf"Dialogue: 0,{offset_millisecond_to_datetime(danmu.start_time)},{offset_millisecond_to_datetime(danmu.end_time)},R2L,,20,20,2,,{{\1c&H10{danmu.color.replace('#', '')},\move({danmu.start_x},{danmu.y},{danmu.end_x},{danmu.y})}}{danmu.content}")
                    self.fp.write("\n")
                    break
                i += 1
            else:
                # print(f"随机放入第{index + 1}条弹幕。{danmu.content}")
                rdm = random.randint(0, len(tracks) - 1)
                tracks[rdm] = danmu
                danmu.y = (rdm + 1) * DANMU_LINE_HEIGHT + DANMU_VIEWPORT_OFFSET_Y

                self.fp.write(
                    rf"Dialogue: 0,{offset_millisecond_to_datetime(danmu.start_time)},{offset_millisecond_to_datetime(danmu.end_time)},R2L,,20,20,2,,{{\1c&H33{danmu.color.replace('#', '')},\move({danmu.start_x},{danmu.y},{danmu.end_x},{danmu.y})}}{danmu.content}")
                self.fp.write("\n")


class AssDanmu:
    def __init__(self, msg_time, content, color, video_start_time):
        # 提供的参数
        self.content = content
        self.color = color
        self.video_start_time = datetime.datetime.strptime(video_start_time, "%Y-%m-%d %H:%M:%S").timestamp() * 1000
        if "." in msg_time:
            msg_time = msg_time[:msg_time.index(".")]

        self.start_time = datetime.datetime.strptime(msg_time,
                                                     "%Y-%m-%d %H:%M:%S").timestamp() * 1000 - self.video_start_time

        self.duration = DANMU_TIME + random.randint(-1000, 1000)

        # 直接计算的参数
        self.end_time = self.start_time + self.duration
        self.end_x = (-get_danmu_width(content)) / 2
        self.start_x = 560 - self.end_x
        self.velocity = (self.start_x - self.end_x) / self.duration

        # 待填写的参数
        self.y = None

    # 判断self能否与danmu_before同轨出现
    # 这里self是追赶的弹幕，danmu_before是被追赶的弹幕
    def compare(self, danmu_before):

        # 首先计算两弹幕的距离。
        # 这里注意，弹幕本身还有长度，需要计算弹幕本身的长度，按一个字符25像素计算
        distance = (self.start_time - danmu_before.start_time) * danmu_before.velocity - (
                get_danmu_width(self.content) + get_danmu_width(danmu_before.content)) / 2

        # 情况1：如果两弹幕的距离小于等于0，则表示刚一出现就重复，不管速度如何，直接返回False。
        if distance <= 0:
            return False

        # 情况2：如果距离大于0（前面已验证过）且速度差值非正，则代表两弹幕距离逐渐增大且恒大于0，可以返回True。
        if self.velocity - danmu_before.velocity <= 0:
            return True

        # 情况3：如果距离与速度差值皆大于0，则计算追赶所需时间，并与最长追赶时间比较。

        # 追赶所需时间 = (两弹幕的距离)/(两弹幕的速度差)
        need_pursue_time = distance / (self.velocity - danmu_before.velocity)
        # 最长追赶时间 = 8秒 - 两弹幕出发的时间差（如果超过该时间，两弹幕皆已出屏幕）
        max_pursue_time = self.duration - (self.start_time - danmu_before.start_time)

        # 如果所需时间大于最长时间，则可以同轨出现；否则不能
        if need_pursue_time > max_pursue_time:
            return True
        else:
            return False
