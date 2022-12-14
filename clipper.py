import os
import datetime
import subprocess
import threading
import re
import time
import traceback
from logger import Logger

from utils import get_video_duration, get_video_real_duration, extract_tags, image_add_text
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
    except subprocess.CalledProcessError as e:
        traceback.print_exc()
        print("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        return e


class ClipThread(threading.Thread):
    def __init__(self, func, args):
        super(ClipThread, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result
        except Exception:
            return None


class Clipper(object):

    def __init__(self, live):
        self.live = live
        self.ffmpeg = self.live.config.get('common', {}).get('ffmpeg_path', '/Users/yujian/ffmpeg')
        self.video_source_dir = self.live.config.get('common', {}).get('video_source_dir', 'video_src')
        self.video_output_dir = self.live.config.get('common', {}).get('video_output_dir', 'video_output')
        self.clip_segment_duration = self.live.config.get('clipper', {}).get('segment_duration', 1800)
        self.split_progress_map = {}

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

    def generate_cover(self, filepath):
        file = os.path.basename(filepath)
        f_split = file.split("_")
        file_start_time_str = (f_split[1] + f_split[2]).replace(".flv", "")
        file_start_time = datetime.datetime.strptime(file_start_time_str, "%Y%m%d%H%M%S")

        duration = get_video_real_duration(filepath)

        start_time = file_start_time
        end_time = start_time + datetime.timedelta(seconds=duration)

        simple_start_time = start_time.strftime("%Y%m%d%H%M%S")
        simple_end_time = end_time.strftime("%Y%m%d%H%M%S")

        cover_file = None
        db = DanmuDB(self.live.room_id)
        danmu_top_list = db.get_top_minute(start_time, end_time)
        if danmu_top_list:
            print(danmu_top_list[:3])
            minute = danmu_top_list[0]["minute"]
            minute_time = datetime.datetime.strptime(minute, "%Y-%m-%d %H:%M:%S")

            content = danmu_top_list[0]["content"]
            keywords = extract_tags(content)

            simple_minute = minute_time.strftime("%Y%m%d%H%M%S")
            cover_file = f"{self.video_output_dir}/{self.live.room_id}/COVER_{simple_start_time}_{simple_end_time}_{simple_minute}.jpg"

            start_offset = (minute_time - file_start_time).seconds
            command = f"{self.ffmpeg} -ss {start_offset}  -i {filepath}  -r 1 -vframes 1 -an  -vcodec mjpeg -loglevel quiet  {cover_file}"
            os.system(command)

            if keywords:
                cover_file = image_add_text(cover_file, keywords, 200, 32)
        return cover_file

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
            cut_duration_time = self.clip_segment_duration
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

    def clip_segment_list(self, filepath):
        video_output_files = []
        duration = get_video_real_duration(filepath)
        for offset in range(0, duration, self.clip_segment_duration):
            start_offset = offset
            end_offset = start_offset + self.clip_segment_duration
            if end_offset > duration:
                end_offset = duration
            self.clip(filepath, start_offset, end_offset)
        return video_output_files

    def clip(self, filepath, start_offset, end_offset):
        is_overlay_danmaku = self.live.room_config.get("clipper", {}).get("overlay_danmaku", False)
        is_hwaccel_enable = self.live.config.get('common', {}).get("hwaccel_enable", False)

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

        command_expand = ""

        hwaccel = " -vsync 0 -hwaccel cuda -hwaccel_output_format cuda -c:v h264_cuvid " if is_hwaccel_enable else ""

        if is_overlay_danmaku:
            video_encoder = "h264_nvenc" if is_hwaccel_enable else "libx264"
            command_expand = f" -vf ass={ass_filepath}   -vf scale_npp=1920:1080 -c:v {video_encoder} -c:a aac  -crf 25 -r 30 "
        else:
            command_expand = " -c:v copy -c:a copy "

        command = f"{self.ffmpeg} {hwaccel} -y  -ss {start_offset}  -t {end_offset - start_offset} -accurate_seek -i {filepath}  {command_expand}  -loglevel quiet  -avoid_negative_ts 1 {output_file}"

        # threading.Thread(target=ffmpeg_command, args=(command,)).start()
        ffmpeg_command(command)

        if os.path.exists(output_file):
            os.remove(ass_filepath)

        return output_file

    def generate_file_title(self, filepath):
        file_name = os.path.basename(filepath)
        f_split = file_name.split("_")
        day = datetime.datetime.strptime(f_split[1], "%Y%m%d").strftime("%Y???%m???%d???")
        return f'???{self.live.room_info["room_owner"]}??? {day} {f_split[2][:2]}??? ???????????? ????????? <{self.live.room_info["room_name"]}>'

    def process_scheduled(self):
        logger = Logger(__name__).get_logger()
        clipper_enable = self.live.room_config.get("clipper", {}).get("enable", False)
        if not clipper_enable:
            return

        while True:
            split_command = self.live.split_command_queue.get()
            filepath = split_command["filepath"]
            is_complete = split_command["is_complete"] if "is_complete" in split_command else False
            if filepath:
                duration = get_video_real_duration(filepath)

                if filepath not in self.split_progress_map:
                    self.split_progress_map[filepath] = {"split_point": 0, "finished_videos": []}

                logger.info(self.live.generate_log(
                    '{} {} {}'.format(split_command, duration, self.split_progress_map[filepath]["split_point"])))

                if is_complete:
                    finished_video = self.clip(filepath,
                                               self.split_progress_map[filepath]["split_point"],
                                               duration)
                    self.split_progress_map[filepath]["split_point"] = duration
                    self.split_progress_map[filepath]["finished_videos"].append(finished_video)

                    cover = self.generate_cover(filepath)
                    self.live.upload_command_queue.put({
                        "title": self.generate_file_title(filepath),
                        "finished_videos": self.split_progress_map[filepath]["finished_videos"],
                        "cover": cover})
                else:
                    if duration - self.split_progress_map[filepath]["split_point"] > self.clip_segment_duration:
                        finished_video = self.clip(filepath,
                                                   self.split_progress_map[filepath]["split_point"],
                                                   self.split_progress_map[filepath][
                                                       "split_point"] + self.clip_segment_duration)

                        self.split_progress_map[filepath]["finished_videos"].append(finished_video)
                        self.split_progress_map[filepath]["split_point"] += self.clip_segment_duration
