import os
import datetime
import subprocess
import re
import threading
import time
import traceback

from utils import get_video_duration, get_video_real_duration
from danmu.DanmuDB import DanmuDB
from danmu.DanmuAss import Ass


def flv2ts(input_file, output_file=None, is_overlying_barrage=False, std_handler=None):
    if not output_file:
        output_file = input_file + ".ts"

    try:
        ret = subprocess.run(
            f"ffmpeg -y -fflags +discardcorrupt -i {input_file} -c copy -bsf:v h264_mp4toannexb -acodec aac -f mpegts {output_file}",
            shell=True, check=True, stdout=std_handler, stderr=std_handler)
        return ret
    except subprocess.CalledProcessError as err:
        traceback.print_exc()
        return err


def concat(merge_conf_path: str, merged_file_path: str, ffmpeg_logfile_handler):
    try:
        ret = subprocess.run(
            f"ffmpeg -y -f concat -safe 0 -i {merge_conf_path} -c copy -fflags +igndts -avoid_negative_ts make_zero {merged_file_path}",
            shell=True, check=True, stdout=ffmpeg_logfile_handler, stderr=ffmpeg_logfile_handler)
        return ret
    except subprocess.CalledProcessError as err:
        traceback.print_exc()
        return err


def ffmpeg_command(command):
    try:
        print(command)
        ret = subprocess.run(command, shell=True, check=True)
        return ret
    except subprocess.CalledProcessError as err:
        traceback.print_exc()
        return err


class Processor(object):
    split_interval = 1800
    split_progress_map = {}

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

    def match_source_video(self, start_time_str, end_time_str):
        start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
        print(start_time, end_time)
        file_match_map = {}
        file_dir = f"{self.video_source_dir}/{self.live.room_id}/"
        for root, dirs, files in os.walk(file_dir):
            for file in files:
                if file.startswith(self.live.room_id) and file.endswith(".flv"):
                    file_duration = get_video_real_duration(file_dir + file)
                    f_split = file.split("_")
                    file_start_time_str = (f_split[1] + f_split[2]).replace(".flv", "")
                    file_start_time = datetime.datetime.strptime(file_start_time_str, "%Y%m%d%H%M%S")
                    file_end_time = file_start_time + datetime.timedelta(seconds=file_duration)
                    print(file_start_time_str, file_duration)

                    if file_start_time <= start_time < file_end_time:
                        if file_dir + file not in file_match_map:
                            file_match_map[file_dir + file] = {"start": 0.0, "end": file_duration}
                        file_match_map[file_dir + file]["start"] = (start_time - file_start_time).total_seconds()

                    if file_start_time <= end_time < file_end_time:
                        if file_dir + file not in file_match_map:
                            file_match_map[file_dir + file] = {"start": 0.0, "end": file_duration}
                        file_match_map[file_dir + file]["end"] = (end_time - file_start_time).total_seconds()

        return file_match_map

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
                command = f"{self.ffmpeg} -ss {start_offset}  -t {end_offset - start_offset} -accurate_seek -y -i {filepath}  -c:v copy -c:a copy -b:v 2M  -avoid_negative_ts 1 {cut_file}"
                print(command)
                os.system(command)
                if os.path.getsize(cut_file) > 10 * 1024 * 1024:
                    cut_files.append(cut_file)
                else:
                    os.remove(cut_file)
        print(cut_files)
        return cut_files

    def process_file(self, filepath, start_offset, end_offset):
        file = os.path.basename(filepath)
        f_split = file.split("_")
        file_start_time_str = (f_split[1] + f_split[2]).replace(".flv", "")
        file_start_time = datetime.datetime.strptime(file_start_time_str, "%Y%m%d%H%M%S")
        start_time = file_start_time + datetime.timedelta(seconds=start_offset)
        end_time = file_start_time + datetime.timedelta(seconds=end_offset)

        start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

        ass_filepath = self.generate_ass(start_time_str, end_time_str, "A")
        output_file = f'{self.video_output_dir}/{self.live.room_id}/{start_time.strftime("%Y%m%d%H%M%S")}_{end_time.strftime("%Y%m%d%H%M%S")}.ass.mp4'

        command = f"{self.ffmpeg} -y  -ss {start_offset}  -t {end_offset - start_offset} -accurate_seek -i {filepath}  -vf ass={ass_filepath} -preset fast -s 1920x1080 -c:v libx264 -c:a aac  -crf 28 -r 30   -avoid_negative_ts 1 {output_file}"

        # threading.Thread(target=ffmpeg_command, args=(command,)).start()
        ffmpeg_command(command)
        return output_file

    def generate_file_title(self, filepath):
        file_name = os.path.basename(filepath)
        f_split = file_name.split("_")
        day = datetime.datetime.strptime(f_split[1], "%Y%m%d").strftime("%Y年%m月%d日")
        return f'【{self.live.room_info["room_owner"]}】 {day} 直播回放 弹幕版 <{self.live.room_info["room_name"]}>'

    def process_scheduled(self):
        while True:
            split_command = self.live.split_command_queue.get()
            filepath = split_command["filepath"]
            is_complete = split_command["is_complete"] if "is_complete" in split_command else False
            if filepath:
                duration = get_video_real_duration(filepath)

                if filepath not in self.split_progress_map:
                    self.split_progress_map[filepath] = {"split_point": 0, "finished_videos": []}

                print(split_command, duration, self.split_progress_map[filepath]["split_point"])

                if is_complete:
                    finished_video = self.process_file(filepath,
                                                       self.split_progress_map[filepath]["split_point"],
                                                       duration)
                    self.split_progress_map[filepath]["split_point"] = duration
                    self.split_progress_map[filepath]["finished_videos"].append(finished_video)

                    self.live.upload_command_queue.put({
                        "title": self.generate_file_title(filepath),
                        "finished_videos": self.split_progress_map[filepath]["finished_videos"]})
                else:
                    if duration - self.split_progress_map[filepath]["split_point"] > self.split_interval:
                        finished_video = self.process_file(filepath,
                                                           self.split_progress_map[filepath]["split_point"],
                                                           self.split_progress_map[filepath][
                                                               "split_point"] + self.split_interval)

                        self.split_progress_map[filepath]["finished_videos"].append(finished_video)
                        self.split_progress_map[filepath]["split_point"] += self.split_interval


class YClass(object):
    _config = {}

    @property
    def config(self):
        import json
        if not self._config:
            with open("config.json", "r") as f:
                self._config = json.load(f)

        return self._config


if __name__ == '__main__':
    lll = YClass()
    setattr(lll, 'room_id', '110')
    processor = Processor(lll)
    # processor.process("2022-11-11 00:20:00", "2022-11-11 01:20:00", "生日快乐")
    # processor.process("2022-11-09 13:48:00", "2022-11-09 14:48:00", "摄像头和马桶")
    # cut_file = processor.cut("2022-11-07 23:10:00", "2022-11-08 01:30:00", "ldc")
    # print(cut_file)
    processor.process_file("/Users/yujian/data/AJRecorder/video/source/110/110_20221116_120012.flv", 0, 1800)
    while True:
        time.sleep(10)
