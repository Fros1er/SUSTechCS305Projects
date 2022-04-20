import sqlite3, time, pprint
import threading
from typing import Dict, List, Tuple

class DamakuSQLLoader:
    conn = sqlite3.connect('test.db', check_same_thread=False)
    insertSQL = "insert into test VALUES(?, ?);"
    mutex = threading.Lock()
    name : str
    
    def __init__(self, name : str) -> None:
        self.name = name
        self.mutex.acquire()
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS %s (
                content text,
                time integer);
                ''' % name)
        self.mutex.release()

    def load(self) -> List[Tuple[str, int]]:
        with self.mutex:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute("select content, time from test order by time;")
                res = cursor.fetchall()
                return res

    def save(self, content: str, time_recv : int) -> None:
        with self.mutex:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(self.insertSQL, [content, time_recv])

class NahelArgama:
    loader = DamakuSQLLoader("test")
    recv_queues : Dict[str, List[Tuple[str, int]]] = {}

    def getHistory(self) -> List[Tuple[str, int]]:
        return self.loader.load()

    def register(self, id : str) -> None:
        self.recv_queues[id] = []

    def send(self, content : str, time_recv) -> None:
        self.loader.save(content, time_recv)
        for key in self.recv_queues:
            self.recv_queues[key].append((content, time_recv))

    def getUnreceived(self, key : str) -> List[Tuple[str, int]]:
        res = self.recv_queues[key]
        self.recv_queues[key] = []
        return res
