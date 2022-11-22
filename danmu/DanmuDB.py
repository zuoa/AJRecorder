import sqlite3


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class DanmuDB(object):
    def __init__(self, room_id):
        self._room_id = room_id
        self._conn = sqlite3.connect(f"danmu.db")
        self._conn.row_factory = dict_factory
        self._cursor = self._conn.cursor()
        self._table_name = f"douyu_{self._room_id}"
        self.create_table()

    def __del__(self):
        self.close()

    def create_table(self):
        self._cursor.execute(f"CREATE TABLE IF NOT EXISTS {self._table_name} \
            ('id' INTEGER PRIMARY KEY autoincrement, \
            'uid' TEXT NOT NULL,'name' TEXT NOT NULL,'badge' TEXT, 'level' INTEGER,\
            'type' TEXT NOT NULL, 'content' TEXT,'color' TEXT,  'room_id' TEXT,\
            'room_owner' TEXT, msg_time TIMESTAMP,\
            'gmt_create' TIMESTAMP default (datetime('now', 'localtime')))")
        self._conn.commit()

    def insert(self, message):
        self._cursor.execute("INSERT INTO " + self._table_name +
                             "('uid', 'name', 'badge', 'level', 'type', 'content', 'color', 'room_id',\
                              'room_owner', 'msg_time')\
                              VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                             (message['uid'], message['nick_name'], message['badge'], message['level'],
                              message['msg_type'],
                              message['content'],
                              message['color'],
                              message['room_id'], message['room_owner'],
                              message['msg_time']))

        self._conn.commit()

    def query(self, start_time, end_time):
        self._cursor.execute(
            f"SELECT * FROM {self._table_name} WHERE msg_time >= '{start_time}' AND msg_time <= '{end_time}' ORDER BY msg_time")
        return self._cursor.fetchall()

    def get_top_minute(self, start_time, end_time):
        self._cursor.execute(
            f"SELECT strftime('%Y-%m-%d %H:%M:00', msg_time) as minute, count(*) as count FROM {self._table_name} WHERE msg_time >= '{start_time}' AND msg_time <= '{end_time}' GROUP BY strftime('%Y-%m-%d %H:%M:00', msg_time) ORDER BY count DESC")
        return self._cursor.fetchall()
    def close(self):
        self._conn.close()
