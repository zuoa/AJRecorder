import websocket
import datetime
import time
import threading
import json
import requests


class DanmuWSClient:
    def __init__(self, on_open, on_message, on_close):
        self.__url = 'wss://danmuproxy.douyu.com:8506/'
        self._on_message = on_message
        self._on_open = on_open
        self._on_close = on_open
        self.__websocket = websocket.WebSocketApp(self.__url,
                                                  on_open=self.__on_open,
                                                  on_message=self.__on_message,
                                                  on_error=self.__on_error,
                                                  on_close=self.__on_close,
                                                  keep_running=True)

    def start(self):
        self.__websocket.run_forever()

    def stop(self):
        self.__websocket.close()

    def send(self, msg):
        msg_compressed = self.__compress_msg(msg)
        msg_encoded = self.__msg_encode(msg_compressed)
        self.__websocket.send(msg_encoded)

    def __on_open(self, ws):
        self._on_open()

    def __on_close(self, ws):
        print('__on_close')
        self._on_close()

    def __on_message(self, ws, msg):
        msg_list_decoded = self.__msg_decode(msg)
        for msg_decoded in msg_list_decoded:
            msg_decompressed = self.__decompress_msg(msg_decoded)
            self._on_message(msg_decompressed)

    def __on_error(self, ws, error):
        print(error)

    def __msg_encode(self, msg):
        # 头部8字节，尾部1字节，与字符串长度相加即数据长度
        # 为什么不加最开头的那个消息长度所占4字节呢？这得问问斗鱼^^
        data_len = len(msg) + 9
        # 字符串转化为字节流
        msg_byte = msg.encode('utf-8')
        # 将数据长度转化为小端整数字节流
        len_byte = int.to_bytes(data_len, 4, 'little')
        # 前两个字节按照小端顺序拼接为0x02b1，转化为十进制即689（《协议》中规定的客户端发送消息类型）
        # 后两个字节即《协议》中规定的加密字段与保留字段，置0
        send_byte = bytearray([0xb1, 0x02, 0x00, 0x00])
        # 尾部以'\0'结束
        end_byte = bytearray([0x00])
        # 按顺序拼接在一起
        data = len_byte + len_byte + send_byte + msg_byte + end_byte
        return data

    def __msg_decode(self, msg_byte):
        '''
        解析斗鱼返回的数据
        :param msg_byte:
        :return:
        '''
        pos = 0
        msg = []
        while pos < len(msg_byte):
            content_length = int.from_bytes(msg_byte[pos: pos + 4], byteorder='little')
            content = msg_byte[pos + 12: pos + 3 + content_length].decode(encoding='utf-8', errors='ignore')
            msg.append(content)
            pos += (4 + content_length)
        return msg

    def __decompress_msg(self, raw_msg):
        res = {}
        attrs = raw_msg.split('/')[0:-1]
        for attr in attrs:
            attr = attr.replace('@s', '/')
            attr = attr.replace('@A', '@')
            couple = attr.split('@=')
            res[couple[0]] = couple[1]
        return res

    def __compress_msg(self, msg_dict):
        msg_seg_list = []
        for k, v in msg_dict.items():
            msg_seg_list.append(str(k) + '@=' + str(v))
        return '/'.join(msg_seg_list) + '/'


class DouyuCore(object):
    """docstring for DouyuClient"""

    def __init__(self, room_id):
        self._room_id = room_id
        self._owner = ''
        self._gift_dict = {}
        self._functionDict = {'other': lambda x: 0}
        self.danmuThread, self.heartThread = None, None
        self.danmu_client = DanmuWSClient(on_open=self.__on_start,
                                          on_message=self.__on_message,
                                          on_close=self.__on_stop)

    def start(self):
        self.danmu_client.start()

    def __on_start(self):
        self._load_room()
        self._join_room_group()
        self._wrap_thread()

    def _join_room_group(self):
        self.danmu_client.send({'type': 'loginreq', 'roomid': self._room_id})
        self.danmu_client.send({'type': 'joingroup', 'rid': self._room_id, 'gid': '-9999'})

    def __on_message(self, msg):
        wrapper_msg = {'original_msg': msg,
                       'room_owner': self._owner,
                       'room_id': self._room_id,
                       'gift_dict': self._gift_dict}
        wrapper_msg['uid'] = msg.get('uid', None)
        wrapper_msg['nick_name'] = msg.get('nn', '')
        wrapper_msg['badge'] = msg.get('bnn', '')
        wrapper_msg['level'] = msg.get('level', None)
        wrapper_msg['content'] = msg.get('txt', '')

        wrapper_msg['msg_time'] = datetime.datetime.fromtimestamp(
            int(int(msg['cst']) / 1000)) if 'cst' in msg else datetime.datetime.now()

        wrapper_msg['msg_type'] = {'dgb': 'gift',
                                   'chatmsg': 'danmu',
                                   'anbc': 'vip',
                                   'uenter': 'enter'}.get(msg['type'], 'other')

        wrapper_msg['gift_id'] = msg.get('gfid', None)
        if wrapper_msg['gift_id'] is not None:
            wrapper_msg['gift_name'] = \
                self._gift_dict.get(wrapper_msg['gift_id'], {'gift_name': '未知礼物' + wrapper_msg['gift_id']})[
                    'gift_name']
            wrapper_msg['gift_count'] = msg.get('gfcnt', 1)
            wrapper_msg['gift_hits'] = msg.get('hits', 1)
            # wrapper_msg['gift_price'] = msg.get('gfs', 0)

        # if "online_vip_list" == msg['type']:
        #     print("-" * 100)
        #     print(msg)
        #     print(decompress_msg(msg["nl"]))

        fn = self._functionDict.get(wrapper_msg['msg_type'], lambda x: 0)
        try:
            fn(wrapper_msg)
        except Exception as ex:
            print(ex)

    def __on_stop(self):
        pass

    def _create_thread_fn(self):
        def _keep_alive(self):
            while True:
                self.danmu_client.send(
                    {'type': 'keeplive', 'tick': int(time.time())})
                # self.danmu_client.send(
                #     {'type': 'sub', 'mt': "online_vip_list"})
                time.sleep(30)

        return _keep_alive

    def _wrap_thread(self):
        heart_beat = self._create_thread_fn()
        self.heartThread = threading.Thread(target=heart_beat, args=(self,))
        self.heartThread.setDaemon(True)
        self.heartThread.start()

    def _load_room(self):
        gift_config1 = requests.get(
            "http://webconf.douyucdn.cn/resource/common/prop_gift_list/prop_gift_config.json").text
        gift_json1 = json.loads(gift_config1.replace('DYConfigCallback(', '')[0:-2])['data']
        for gid, ginfo in gift_json1.items():
            self._gift_dict[gid] = {'gift_id': gid, 'gift_name': ginfo['name']}

        gift_config2 = requests.get(
            "https://webconf.douyucdn.cn/resource/common/gift/gift_template/20728.json").text
        gift_list2 = json.loads(gift_config2.replace('DYConfigCallback(', '')[0:-2])['data']
        for g in gift_list2:
            self._gift_dict[g["id"]] = {'gift_id': g["id"], 'gift_name': g['name']}


class DouyuClient(DouyuCore):
    """docstring for """

    def __init__(self, room_id):
        # global __table_name
        super(DouyuClient, self).__init__(room_id)
        print(room_id)

    def __register(self, fn, msg_type):
        if fn is None:
            if msg_type == 'default':
                self._functionDict['default'] = lambda x: 0
            elif self._functionDict.get(msg_type):
                del self._functionDict[msg_type]
        else:
            self._functionDict[msg_type] = fn

    def default(self, fn):
        self.__register(fn, 'default')
        return fn

    def danmu(self, fn):
        self.__register(fn, 'danmu')
        return fn

    def gift(self, fn):
        self.__register(fn, 'gift')
        return fn

    def enter(self, fn):
        self.__register(fn, 'enter')
        return fn

    def anbc(self, fn):
        self.__register(fn, 'vip')
        return fn



