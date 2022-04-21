import sqlite3
import threading
import uuid
import time
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
    recvQueues: Dict[str, Dict[str, List]] = {}

    # lock for limit each video or livestream
    recvLocks: Dict[str, threading.Lock] = {}

    # dict for memorize last quried time for each client
    uuidUpdateTimes: Dict[str, Dict[str, float]] = {}

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
        if videoName not in self.recvQueues:
            self.recvQueues[videoName] = {}
            self.uuidUpdateTimes[videoName] = {}
            self.recvLocks[videoName] = threading.Lock()
        key = uuid.uuid4()  # gen unduplicated uuid
        while key in self.recvQueues[videoName]:
            key = uuid.uuid4()
        self.recvQueues[videoName][str(key)] = []
        self.uuidUpdateTimes[videoName][str(key)] = time.time()
        return str(key)

    def sendVideoDanmaku(self, videoName: str, content: str, time_recv) -> None:
        '''
        save one danmaku to database and all recv_queues bind to videoName.
        '''
        self.loader.save(videoName, content, time_recv)
        if videoName not in self.recvQueues:
            return
        t = time.time()
        with self.recvLocks[videoName]:
            for key in self.recvQueues[videoName]:
                # if client didn't poll for 30s
                if self.uuidUpdateTimes[videoName][key] - t > 30:
                    del self.uuidUpdateTimes[videoName][key]
                    del self.recvQueues[videoName][key]  # remove it's list
                    continue
                self.recvQueues[videoName][key].append(
                    (content, time_recv))  # content & time

    def sendLiveDanmaku(self, liveName: str, content: str) -> None:
        '''
        save one danmaku to all recv_queues bind to videoName, as live danmaku doesn't need to be store.
        '''
        if liveName not in self.recvQueues:
            return
        with self.recvLocks[liveName]:
            for key in self.recvQueues[liveName]:
                self.recvQueues[liveName][key].append(content)  # content only

    def getUnreceived(self, videoName: str, key: str) -> List:
        '''
        get all unreceived danmaku for videoName and uuid(key) together, return them and clear the queue.
        '''
        with self.recvLocks[videoName]:
            self.uuidUpdateTimes[videoName][key] = time.time()  # update time
            res = self.recvQueues[videoName][key]
            self.recvQueues[videoName][key] = []
        return res
