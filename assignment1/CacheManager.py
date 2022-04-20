from typing import Optional, Any, Dict, Tuple
import time, threading
from RWLock import RWLock

class Cache:
    """
    Cache class with content and ttl
    """
    invalidTime : float
    content : Any
    def __init__(self, content : Any, ttl : float):
        self.content = content
        self.invalidTime = time.time() + ttl
        threading.Thread

class CacheManager():
    """
    Thread safe cache manager
    """
    # RWLock from third party lib in RWLock.py
    lock = RWLock()
    contents : Dict[str, Cache]

    def __init__(self, interval : int = 300):
        self.contents = {}
        threading.Thread(target=self._invalidateCache, args=(interval,)).start()

    def readCache(self, key : str) -> Optional[Tuple[Any, float]]:
        """
        Read Cache by key. Return None on outdated or not found.
        If content's outdated, delete the content.
        """
        content = None
        self.lock.reader_acquire()
        if key in self.contents:
            content = self.contents[key]
        self.lock.reader_release()
        if content is None:
            return None
        timeRemaining = content.invalidTime - time.time()
        if timeRemaining <= 0:
            self.lock.writer_acquire()
            del self.contents[key]
            self.lock.writer_release()
            return None
        return content.content, timeRemaining

    def writeCache(self, key : str, content : Any, ttl : float):
        """
        Add to cache. If key is present, override the content.
        """
        self.lock.writer_acquire()
        self.contents[key] = Cache(content, ttl)
        self.lock.writer_release()

    def _invalidateCache(self, interval : int) -> None:
        """
        Delete outdated items.
        """
        self.lock.writer_acquire()
        t = time.time()
        for key in self.contents:
            if self.contents[key].invalidTime - t <= 0:
                del self.contents[key]
        self.lock.writer_release()
        time.sleep(interval)

    def __str__(self) -> str:
        res = ""
        self.lock.reader_acquire()
        if len(self.contents) > 0:
            t = time.time()
            for key in self.contents:
                timeRemaining = self.contents[key].invalidTime - t
                if timeRemaining > 0:
                    res += "%s: %s, expires after %f sec\n" % (key, self.contents[key].content, timeRemaining)
        else:
            res = "Cache is empty"
        self.lock.reader_release()
        return res
