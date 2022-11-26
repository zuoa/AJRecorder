import json
from multiprocessing import Process

from DouyuLive import DouyuLive


def run(room_config):
    live = DouyuLive(room_config)
    live.start()


if __name__ == '__main__':
    with open("rooms.json", "r") as f:
        rooms = json.load(f)
        room_process_list = []
        for room_config in rooms:
            if room_config.get("enable", False):
                process = Process(target=run, args=(room_config,))
                process.daemon = True
                process.start()
                room_process_list.append(process)

        for p in room_process_list:
            p.join()
