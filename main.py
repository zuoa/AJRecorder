from multiprocessing import Process

from DouyuLive import DouyuLive


def run(room_id, room_tags):
    live = DouyuLive(room_id, room_tags)
    live.start()


if __name__ == '__main__':

    room_map = {
        '73965': ['孙正'],
        '7828414': ['煊宝'],
        '7930707': ['朴雨彬']
    }

    for room_id, room_tags in room_map.items():
        process = Process(target=run, args=(room_id, room_tags,))
        process.start()
