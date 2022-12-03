import time
import json
from danmu.DanmuAss import Ass

json_file = "/Users/yujian/Downloads/2022-12-02 16-21 煊里奥历险记~～～.json"

with open(json_file) as f:
    all_content = f.read()
    json_content = json.loads(all_content)
    print(1)
    danmu_list = []
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(json_content['meta']['recordStartTimestamp'] / 1000))
    end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(json_content['meta']['recordStopTimestamp'] / 1000))
    for msg in json_content["messages"]:
        if msg['type'] != 'comment':
            continue

        dm = {}
        dm["content"] = msg["text"]
        dm["msg_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(msg["timestamp"] / 1000))
        dm["color"] = "#FFFFFF"
        danmu_list.append(dm)

    Ass(danmu_list, start_time, './json2ass/111.ass').flush()
