import os
import struct
import time


class FlvParser(object):
    def __init__(self, path):
        self.path = path
        self.fp = open(path, "rb")
        self.file_size = os.path.getsize(path)
        self.parse_header()
        self.duration = 0
        # self.tag_list = self.parse_tag_list()

    def parse_header(self):
        self.fp.read(13)

    def parse_tag_list(self):
        tag_list = []
        self.duration = 0
        is_first_video_tag = False
        first_ts = 0
        while self.fp.tell() < self.file_size:
            tag_header = self.fp.read(11)
            tag_type = tag_header[0]
            tag_data_size = int.from_bytes(tag_header[1:4], 'big')
            tag_ts = int.from_bytes(tag_header[4:7], 'big')
            # print(tag_type)
            # print(tag_data_size)
            tag_data = self.fp.read(tag_data_size)
            tag_size = int.from_bytes(self.fp.read(4), 'big')

            if tag_type == 9:
                if not is_first_video_tag:
                    # print(tag_data[1])
                    if tag_data[1] == 1:
                        is_first_video_tag = True
                        first_ts = tag_ts

                print(f"tag_data_size:{tag_data_size}, tag_ts:{tag_ts}")

                # print(int.from_bytes(tag_data[2:5], 'big'))
                self.duration += int.from_bytes(tag_data[2:5], 'big')
                # print(tag_size)
                print("-" * 100)
        print(first_ts)
        print(f'{self.duration / 1000:.2f}')
        return tag_list

    def get_duration(self):
        self.fp.seek(13)
        first_ts = -1
        last_ts = -1
        self.duration = 0
        while self.fp.tell() < self.file_size:
            tag_header = self.fp.read(11)
            tag_type = tag_header[0]
            tag_data_size = int.from_bytes(tag_header[1:4], 'big')
            tag_ts = int.from_bytes(tag_header[4:7], 'big')
            tag_data = self.fp.read(tag_data_size)
            tag_size = int.from_bytes(self.fp.read(4), 'big')
            if tag_type == 9 and tag_data[1] == 1:
                if first_ts < 0:
                    first_ts = tag_ts
                if tag_ts >= first_ts:
                    last_ts = tag_ts
                else:
                    self.duration += last_ts - first_ts
                    first_ts = tag_ts
                    # print(tag_ts)
        # print(first_ts, last_ts)
        self.duration += last_ts - first_ts

        return self.duration / 1000


if __name__ == '__main__':
    from utils import get_video_duration

    file = "/Users/yujian/data/AJRecorder/video/source/7828414/7828414_20221115_231637.flv"
    parser = FlvParser(file)
    print(time.time())
    print(parser.get_duration())
    print(time.time())
    print(get_video_duration(file))

    print(time.time())
    # parser.parse_tag_list()
