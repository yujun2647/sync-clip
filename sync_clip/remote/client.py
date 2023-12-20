"""
 accept remote sync signal
 send signal to remote
"""
import sys
import logging
import pickle
import socket
import time
import traceback
from queue import Queue

from sync_clip.stuff.sync_signal import *
from sync_clip.utils.util_thread import new_thread

logger = logging.getLogger("sync_clip")


class Client(object):

    def __init__(self, host="0.0.0.0", port=12364):
        self.host = host
        self.port = port
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._check_connection()
        self.is_closed = True
        self.recv_sync_sig = Queue()

    def _check_connection(self):
        self.send_sync_data(ConCheck())
        self.udp_socket.settimeout(1)
        try:
            response, addr = self.udp_socket.recvfrom(1024)
            print("confirmed connection !!!")
        except socket.timeout:
            print(f"\n\n unable to connect to remote server "
                  f"`{self.host}:{self.port}` !!! \n")
            sys.exit(1)

    def send_sync_data(self, signal: SyncSignal):
        p_sync_data = pickle.dumps(signal)
        try:
            self.udp_socket.sendto(p_sync_data, (self.host, self.port))
        except Exception as exp:
            logger.error(f"sending sync data error: {exp} "
                         f"\n{traceback.format_exc()}")

    @new_thread
    def _keep_receiving(self):
        while not self.is_closed:
            # noinspection PyBroadException
            try:
                self.udp_socket.settimeout(0.5)
                response, addr = self.udp_socket.recvfrom(1024 * 1024 * 5)
                sig: SyncSignal = pickle.loads(response)
                if isinstance(sig, SyncData):
                    self.recv_sync_sig.put(sig)

            except socket.timeout:
                continue
            except Exception as exp:
                logger.error(f"Exception while receiving: {exp}\n"
                             f"{traceback.format_exc()}")
                continue

    @new_thread
    def _keep_alive(self):
        while not self.is_closed:
            self.send_sync_data(HeartbeatSignal())
            time.sleep(1)

    def start(self):
        self.is_closed = False
        self._keep_receiving()
        self._keep_alive()

    def close(self):
        self.is_closed = True


if __name__ == "__main__":
    import sys
    from queue import Empty

    tc = Client()
    tc.start()
    i = 0
    while True:
        try:
            tc.send_sync_data(SyncData(f"{sys.argv[1]}-{i}"))
            _sig: SyncData = tc.recv_sync_sig.get(timeout=1)
            print(f"receive from server: {_sig.data}")
            time.sleep(1)
            i += 1
        except Empty:
            continue
