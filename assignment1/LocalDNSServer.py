import socket
import threading
from DNSHandler import DNSHandler
from socket import socket as Socket
from concurrent.futures import ThreadPoolExecutor

class DNSServer:

    socket : Socket
    dnsHandler : DNSHandler
    threadPool : ThreadPoolExecutor
    lock : threading.Lock

    def __init__(self, ip: str = '127.0.0.1', port: int = 5533):
        self.socket = Socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((ip, port))
        self.dnsHandler = DNSHandler()
        self.threadPool = ThreadPoolExecutor(4, "DNSServer_")
        self.lock = threading.Lock()

    def start(self):
        while True:
            msg, addr = self.receive()
            # request a thread from threadpool to handle the query
            self.threadPool.submit(self.reply, msg, addr)

    def receive(self):
        return self.socket.recvfrom(8192)

    def reply(self, msg, address) -> None:
        # parse dns packet and send
        res = self.dnsHandler.handle(msg)
        with self.lock:
            self.socket.sendto(res, address)


if __name__ == '__main__':
    input('Enter your ip: ')
    input('Enter your port: ')
    local_dns_server = DNSServer()
    local_dns_server.start()
