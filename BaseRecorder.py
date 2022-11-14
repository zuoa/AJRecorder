import os
import re
import time

import requests
import datetime
from logger import Logger


class BaseRecorder:
    def __init__(self):
        self.logger = Logger(__name__).get_logger()

    def record(self, record_url: str, output_filename: str) -> None:
        self.logger = Logger(__name__).get_logger()
        self.logger.info('Start recording...')

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
                                timeout=config.get('root', {}).get('check_interval', 60))
            with open(output_filename, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        f.flush()
        except Exception as e:
            self.logger.error('Error while recording:' + str(e))

        self.logger.info('Stop recording...')

    def generate_filename(self, live) -> str:
        video_source_dir = live.config.get('common', {}).get('video_source_dir', 'video_src')
        filepath = f"{video_source_dir}/{live.room_id}/{live.room_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.flv"
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        return filepath

    def run(self, live, command_queue):
        while True:
            if live.live_status:
                live_url = live.live_url
                if live_url:
                    record_filepath = self.generate_filename(live)
                    self.record(live_url, record_filepath)
                    time.sleep(5)
                    if os.path.getsize(record_filepath) > 1024 * 1024:
                        command_queue.put({'type': 'full', 'filepath': record_filepath})
                    else:
                        os.remove(record_filepath)
                    continue

            time.sleep(30)
