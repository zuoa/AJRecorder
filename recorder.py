import os
import re
import time

import requests
import datetime
from logger import Logger


class FlvRecorder:
    def __init__(self, live):
        self.logger = Logger(__name__).get_logger()
        self.live = live
        self.last_notify_ts = time.time()

    def record(self, record_url: str, output_filename: str) -> None:
        self.logger = Logger(__name__).get_logger()
        self.logger.info(self.live.generate_log('Start recording...'))
        self.last_notify_ts = time.time()

        try:
            config = {}
            default_headers = {
                'Accept-Encoding': 'identity',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36 ',
                'Referer': re.findall(
                    r'(https://.*\/).*\.flv',
                    record_url)[0]
            }
            headers = {**default_headers, **config.get('root', {}).get('request_header', {})}

            resp = requests.get(record_url, stream=True,
                                headers=headers,
                                timeout=60)
            with open(output_filename, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        f.flush()
                        # print(len(chunk))

                        ts = time.time()
                        if ts - self.last_notify_ts > 60 * 16:
                            self.live.split_command_queue.put({"filepath": output_filename})
                            self.last_notify_ts = ts
        except Exception as e:
            self.logger.error(self.live.generate_log('Error while recording:' + str(e)))

        self.logger.info(self.live.generate_log('Stop recording...'))

    def generate_filename(self, live) -> str:
        video_source_dir = live.config.get('common', {}).get('video_source_dir', 'video_src')
        filepath = f"{video_source_dir}/{live.room_id}/{live.room_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.flv"
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        return filepath

    def run(self):
        while True:
            live = self.live
            if live.live_status:
                live_url = live.live_url
                if live_url:
                    live.recording_file = self.generate_filename(live)
                    self.record(live_url, live.recording_file)
                    time.sleep(5)
                    if os.path.getsize(live.recording_file) > 10 * 1024 * 1024:
                        self.live.split_command_queue.put({"filepath": live.recording_file, "is_complete": True})
                    else:
                        os.remove(live.recording_file)

                    continue

            time.sleep(30)
