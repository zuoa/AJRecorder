from douyu import DouyuLive


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    for room in ['7828414']:
        live = DouyuLive(room)
        live.start()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
