import os
import struct


class FlvParser(object):
    def __init__(self, path):
        self.path = path
        self.fp = open(path, "rb")
        self.file_size = os.path.getsize(path)
        self.parse_header()
        self.duration = 0
        self.tag_list = self.parse_tag_list()

    def parse_header(self):
        print(self.fp.read(13))

    def parse_tag_list(self):
        tag_list = []
        self.duration = 0
        is_first_video_tag = False
        while self.fp.tell() < self.file_size:
            tag_header = self.fp.read(11)
            tag_type = tag_header[0]
            tag_data_size = int.from_bytes(tag_header[1:4], 'big')
            # print(tag_type)
            # print(tag_data_size)
            tag_data = self.fp.read(tag_data_size)
            tag_size = int.from_bytes(self.fp.read(4), 'big')

            if tag_type == 9:
                if not is_first_video_tag:
                    # print(tag_data[1])
                    if tag_data[1] == 1:
                        is_first_video_tag = True
                # print(int.from_bytes(tag_header[1:4], 'big'))
                # print(int.from_bytes(tag_header[4:7], 'big'))
                self.duration += int.from_bytes(tag_data[2:5], 'big')
                # print(tag_size)
                # print("-" * 100)
        print(f'{self.duration / 1000:.2f}')
        return tag_list

    def get_duration(self):
        return self.duration / 1000


if __name__ == '__main__':
    from utils import get_video_duration

    file = "video_src/73965/73965_20221111_174822.flv"
    parser = FlvParser(file)
    print(parser.get_duration())
    print(get_video_duration(file))
    # parser.parse_tag_list()
