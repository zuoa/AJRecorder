from douyu import DouyuLive


if __name__ == '__main__':
    for room in ['73965', '7828414']:
        live = DouyuLive(room)
        live.start()


