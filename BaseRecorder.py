import re
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
            # logging.info(self.generate_log('√ 正在录制...' + self.room_id))
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
                                timeout=config.get(
                                    'root', {}).get('check_interval', 60))
            with open(output_filename, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        except Exception as e:
            self.logger.error('Error while recording:' + str(e))

        self.logger.info('Stop recording...')

    def generate_filename(self, room_id: str) -> str:
        return f"{room_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.flv"

    def run(self, live):
        while True:
            self.record(live.live_url, self.generate_filename(live.room_id))
