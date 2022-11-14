from douyu import DouyuLive

if __name__ == '__main__':

    room_map = {
        '73965': ['孙正'],
        '7930707': ['朴雨彬']
    }

    for room_id, room_tags in room_map.items():
        live = DouyuLive(room_id, room_tags)
        live.start()
