import sqlite3
import threading
import uuid
from typing import Dict, List, Tuple


class DamakuSQLLoader:
    '''
    Util class for connecting to sqlite
    '''
    # sql connction and lock
    # Write to sqlite is single threaded
    conn = sqlite3.connect('test.db', check_same_thread=False)
    mutex = threading.Lock()

    insertSQL = "insert into %s VALUES(?, ?);"

    def addVideo(self, videoName: str):
        '''
        if video not in db before, create new table
        '''
        with self.mutex:
            with self.conn:
                self.conn.execute('''CREATE TABLE IF NOT EXISTS %s (
                    content text,
                    time integer);
                    ''' % videoName)

    def load(self, videoName: str) -> List[Tuple[str, int]]:
        '''
        load all existed danmaku of a video from db
        '''
        with self.mutex:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(
                    "select content, time from %s order by time;" % videoName)
                return cursor.fetchall()

    def save(self, videoName: str, content: str, time_recv: int) -> None:
        '''
        save one danmaku to db
        '''
        with self.mutex:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(self.insertSQL %
                               videoName, [content, time_recv])


class NahelArgama:
    '''
    Danmaku Manager for both livestream and video for html.
    Named from https://gundam.fandom.com/wiki/SCVA-76_Nahel_Argama
    '''
    loader = DamakuSQLLoader()
    # All danmakus to be send via http store here.
    # Structure: {"video or livestream name" : {
    #   "uuid for http client": List[]
    # }}
    # List contants danmaku's content and time for video, content only for livestream.
    recv_queues: Dict[str, Dict[str, List]] = {}

    def getHistory(self, videoName: str) -> List:
        '''
        :returns: all sorted existed danmaku of a video from db
        '''
        return self.loader.load(videoName)

    def registerVideo(self, videoName: str) -> None:
        '''
        create table matching videoName if not exists in db.
        '''
        self.loader.addVideo(videoName)

    def register(self, videoName: str, isVideo: bool = True) -> str:
        '''
        register live or video to manager for html querys.
        :returns: uuid for later html polling 
        '''
        if isVideo:
            self.registerVideo(videoName)
        if videoName not in self.recv_queues:
            self.recv_queues[videoName] = {}
        key = uuid.uuid4()  # gen unduplicated uuid
        while key in self.recv_queues[videoName]:
            key = uuid.uuid4()
        self.recv_queues[videoName][str(key)] = []
        return str(key)

    def sendVideoDanmaku(self, videoName: str, content: str, time_recv) -> None:
        '''
        save one danmaku to database and all recv_queues bind to videoName.
        '''
        self.loader.save(videoName, content, time_recv)
        if videoName not in self.recv_queues:
            return
        for key in self.recv_queues[videoName]:
            self.recv_queues[videoName][key].append(
                (content, time_recv))  # content & time

    def sendLiveDanmaku(self, liveName: str, content: str) -> None:
        '''
        save one danmaku to all recv_queues bind to videoName, as live danmaku doesn't need to be store.
        '''
        if liveName not in self.recv_queues:
            return
        for key in self.recv_queues:
            self.recv_queues[liveName][key].append(content)  # content only

    def getUnreceived(self, videoName: str, key: str) -> List:
        '''
        get all unreceived danmaku for videoName and uuid(key) together, return them and clear the queue.
        '''
        res = self.recv_queues[videoName][key]
        self.recv_queues[videoName][key] = []
        return res
