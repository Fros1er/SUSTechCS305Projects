import sqlite3, threading, uuid
from typing import Dict, List, Tuple

class DamakuSQLLoader:
    conn = sqlite3.connect('test.db', check_same_thread=False)
    insertSQL = "insert into %s VALUES(?, ?);"
    mutex = threading.Lock()

    def addVideo(self, videoName : str):
        with self.mutex:
            with self.conn:
                self.conn.execute('''CREATE TABLE IF NOT EXISTS %s (
                    content text,
                    time integer);
                    ''' % videoName)

    def load(self, videoName : str) -> List[Tuple[str, int]]:
        with self.mutex:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute("select content, time from %s order by time;" % videoName)
                return cursor.fetchall()

    def save(self, videoName : str, content: str, time_recv : int) -> None:
        with self.mutex:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(self.insertSQL % videoName, [content, time_recv])

class NahelArgama:
    loader = DamakuSQLLoader()
    recv_queues : Dict[str, Dict[str, List]] = {}

    def getHistory(self, name : str) -> List:
        return self.loader.load(name)

    def register(self, videoName : str, isVideo : bool = True) -> str:
        if isVideo:
            self.loader.addVideo(videoName)
        if videoName not in self.recv_queues:
            self.recv_queues[videoName] = {}
        key = uuid.uuid4()
        while key in self.recv_queues[videoName]:
            key = uuid.uuid4()
        self.recv_queues[videoName][str(key)] = []
        return str(key)

    def sendVideo(self, videoName : str, content : str, time_recv) -> None:
        self.loader.save(videoName, content, time_recv)
        if videoName not in self.recv_queues:
            return
        for key in self.recv_queues[videoName]:
            self.recv_queues[videoName][key].append((content, time_recv))

    def sendLive(self, liveName : str, content : str) -> None:
        if liveName not in self.recv_queues:
            return
        for key in self.recv_queues:
            self.recv_queues[liveName][key].append(content)

    def getUnreceived(self, videoName : str, key : str) -> List:
        res = self.recv_queues[videoName][key]
        self.recv_queues[videoName][key] = []
        return res
