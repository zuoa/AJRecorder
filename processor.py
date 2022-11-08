import os
import datetime
import sqlite3
import re

from utils import get_video_duration
from danmu.DanmuDB import DanmuDB
from danmu.DanmuAss import Ass


class Processor(object):
    def __init__(self, live, config):
        self.ffmpeg = "/Users/yujian/ffmpeg"
        self.live = live
        self.config = config

    def find_source_video(self, start_time_str, end_time_str):
        start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")

        file_dir = f"video_src/{self.live.room_id}/"
        for root, dirs, files in os.walk(file_dir):
            for file in files:
                if file.endswith(".flv"):
                    f_split = file.split("_")
                    file_start_time_str = (f_split[1] + f_split[2]).replace(".flv", "")
                    file_start_time = datetime.datetime.strptime(file_start_time_str, "%Y%m%d%H%M%S")
                    file_end_time = file_start_time + datetime.timedelta(seconds=get_video_duration(file_dir + file))
                    print(file)
                    print(file_start_time)
                    print(file_end_time)

                    if file_start_time <= start_time < file_end_time:
                        return file_dir + file, (start_time - file_start_time).total_seconds(), (
                                end_time - file_start_time).total_seconds()
        return None, None, None

    def cut(self, start_time, end_time, tag):
        input_file, start_offset, end_offset = self.find_source_video(start_time, end_time)
        if not input_file:
            return

        simple_start_time = re.sub("\D", "", start_time)
        simple_end_time = re.sub("\D", "", end_time)
        output_file = f"dist/{self.live.room_id}/{tag}_{simple_start_time}_{simple_end_time}.mp4"
        if not os.path.exists(os.path.dirname(output_file)):
            os.makedirs(os.path.dirname(output_file))

        command = f"{self.ffmpeg} -ss {start_offset}  -t {end_offset - start_offset} -i {input_file}  -vcodec copy -acodec copy {output_file}"
        print(command)
        os.system(command)

        return output_file

    def generate_ass(self, start_time, end_time, tag):
        simple_start_time = re.sub("\D", "", start_time)
        simple_end_time = re.sub("\D", "", end_time)
        ass_file = f"dist/{self.live.room_id}/{tag}_{simple_start_time}_{simple_end_time}.ass"

        db = DanmuDB(self.live.room_id)
        danmu_list = db.query(start_time, end_time)
        ass = Ass(danmu_list, start_time, ass_file)
        ass.flush()

        return ass_file

    def process(self, start_time, end_time, tag):
        video_file_path = self.cut(start_time, end_time, tag)
        if not video_file_path:
            return
        ass_file_path = self.generate_ass(start_time, end_time, tag)
        command = f"{self.ffmpeg} -i {video_file_path}  -vf ass={ass_file_path} -threads 4 -preset fast -c:a copy {video_file_path}.withass.mp4"
        print(command)
        os.system(command)


class YClass(object):
    pass


if __name__ == '__main__':
    lll = YClass()
    setattr(lll, 'room_id', '73965')
    processor = Processor(lll, None)
    processor.process("2022-11-08 12:30:00", "2022-11-08 12:40:00", "test")
    # cut_file = processor.cut("2022-11-07 23:10:00", "2022-11-08 01:30:00", "ldc")
    # print(cut_file)
