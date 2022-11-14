import os
import datetime
import sqlite3
import re

from utils import get_video_duration, get_video_real_duration
from danmu.DanmuDB import DanmuDB
from danmu.DanmuAss import Ass


class Processor(object):
    def __init__(self, live):
        self.live = live
        self.ffmpeg = self.live.config.get('common', {}).get('ffmpeg_path', '/Users/yujian/ffmpeg')
        self.video_source_dir = self.live.config.get('common', {}).get('video_source_dir', 'video_src')
        self.video_output_dir = self.live.config.get('common', {}).get('video_output_dir', 'video_output')

    def find_source_video(self, start_time_str, end_time_str):
        start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")

        file_dir = f"{self.video_source_dir}/{self.live.room_id}/"
        for root, dirs, files in os.walk(file_dir):
            for file in files:
                if file.startswith(self.live.room_id) and file.endswith(".flv"):
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
        output_file = f"{self.video_output_dir}/{self.live.room_id}/{tag}_{simple_start_time}_{simple_end_time}.mp4"
        if not os.path.exists(os.path.dirname(output_file)):
            os.makedirs(os.path.dirname(output_file))

        command = f"{self.ffmpeg} -ss {start_offset}  -t {end_offset - start_offset} -i {input_file}   -vcodec copy -acodec copy {output_file}"
        print(command)
        os.system(command)

        return output_file

    def generate_ass(self, start_time, end_time, tag):
        simple_start_time = re.sub("\D", "", start_time)
        simple_end_time = re.sub("\D", "", end_time)
        ass_file = f"{self.video_output_dir}/{self.live.room_id}/{tag}_{simple_start_time}_{simple_end_time}.ass"

        db = DanmuDB(self.live.room_id)
        danmu_list = db.query(start_time, end_time)
        ass = Ass(danmu_list, start_time, ass_file)
        ass.flush()

        return ass_file

    def process(self, start_time, end_time, tag):
        video_filepath = self.cut(start_time, end_time, tag)
        if not video_filepath:
            return
        ass_filepath = self.generate_ass(start_time, end_time, tag)
        command = f"{self.ffmpeg} -y -i {video_filepath} -r 30 -b:v 4M -vf ass={ass_filepath} -threads 4 -preset fast -c:a copy {video_filepath}.withass.mp4"
        print(command)
        os.system(command)

    def cut_file(self, filepath):

        cut_files = []
        file_name = os.path.basename(filepath)
        if file_name.startswith(self.live.room_id) and file_name.endswith(".flv"):
            f_split = file_name.split("_")
            duration = int(get_video_real_duration(filepath))
            cut_duration_time = 1800
            for offset in range(0, duration, cut_duration_time):
                start_offset = offset
                end_offset = start_offset + cut_duration_time
                if end_offset >= duration:
                    end_offset = duration
                cut_file = f"{self.video_output_dir}/{self.live.room_id}/{f_split[1]}/{file_name}.P{int(start_offset / cut_duration_time) + 1}.mp4"
                if not os.path.exists(os.path.dirname(cut_file)):
                    os.makedirs(os.path.dirname(cut_file))
                # command = f"{self.ffmpeg} -ss {start_offset}  -t {end_offset - start_offset} -y -i {filepath} -threads 4 -preset fast  -c:v libx264 -c:a copy  -crf 28 -r 30 {cut_file}"
                command = f"{self.ffmpeg} -ss {start_offset}  -t {end_offset - start_offset} -accurate_seek -y -i {filepath} -c:v copy -c:a copy -b:v 2M  -avoid_negative_ts 1 {cut_file}"
                print(command)
                os.system(command)
                if os.path.getsize(cut_file) > 10 * 1024 * 1024:
                    cut_files.append(cut_file)
                else:
                    os.remove(cut_file)
        print(cut_files)
        return cut_files

    def process_file(self, filepath):
        self.cut_file(filepath)


class YClass(object):
    pass


if __name__ == '__main__':
    lll = YClass()
    setattr(lll, 'room_id', '73965')
    processor = Processor(lll, None)
    # processor.process("2022-11-11 00:20:00", "2022-11-11 01:20:00", "生日快乐")
    # processor.process("2022-11-09 13:48:00", "2022-11-09 14:48:00", "摄像头和马桶")
    # cut_file = processor.cut("2022-11-07 23:10:00", "2022-11-08 01:30:00", "ldc")
    # print(cut_file)
    processor.process_file("/Users/yujian/Code/py/AJRecorder/video_src/73965/73965_20221111_123152.flv")
