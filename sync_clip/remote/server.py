"""
接收远程的注册信息, 并记录

接收远程的信号同步信息, 并广播给其他人


"""
import pickle
import socket
import logging
import time
import traceback
from queue import Queue

from sync_clip.stuff.sync_signal import *
from sync_clip.utils.util_thread import new_thread

logger = logging.getLogger("sync_clip")


class ClientSet(object):

    def __init__(self):
        self.set = {}

    def update_client(self, addr: tuple):
        self.set[addr] = time.time()
        expired_clients = []
        for addr, last_htime in self.set.items():
            if time.time() - last_htime > 3:
                expired_clients.append(addr)
        for addr in expired_clients:
            self.set.pop(addr)


class Server(object):
    def __init__(self, host="0.0.0.0", port=12364):
        self.host = host
        self.port = port
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((self.host, self.port))
        self.client_heartbeat_q = Queue()
        self.sending_msg_queue = Queue()
        self.is_closed = True
        self.client_set = {}

    def _update_client(self, addr: tuple):
        self.client_set[addr] = time.time()

    @new_thread
    def _monitor_expired_clients(self):
        while not self.is_closed:
            expired_clients = []
            for addr, last_htime in self.client_set.items():
                if time.time() - last_htime > 3:
                    expired_clients.append(addr)
            for addr in expired_clients:
                self.client_set.pop(addr)
            time.sleep(3)

    def _broadcast_sync_data(self, sig: SyncData, this_addr: tuple):
        for addr in self.client_set.keys():
            if addr != this_addr:
                self._send_sync_data(sig, addr)

    def _send_sync_data(self, sig: SyncSignal, addr: tuple):
        p_sync_data = pickle.dumps(sig)
        try:
            self.udp_socket.sendto(p_sync_data, addr)
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
                assert isinstance(sig, SyncSignal)

                if isinstance(sig, ConCheck):
                    self._send_sync_data(sig, addr)
                    self._update_client(addr)
                elif isinstance(sig, HeartbeatSignal):
                    self._update_client(addr)
                elif isinstance(sig, SyncData):
                    self._broadcast_sync_data(sig, addr)

            except socket.timeout:
                continue
            except Exception as exp:
                logger.error(f"Exception while receiving: {exp}\n"
                             f"{traceback.format_exc()}")
                continue

    def start(self):
        self.is_closed = False
        self._keep_receiving()
        self._monitor_expired_clients()
        logger.info(f"\n\n\t[Server started] listening on "
                    f"`{self.host}:{self.port}`")

    def close(self):
        self.is_closed = True


def server(port=12364):
    from sync_clip.utils.util_log import set_scripts_logging

    set_scripts_logging(__file__, logger=logger, level=logging.DEBUG,
                        console_log=True, file_mode="a")
    Server(port=port).start()


if __name__ == "__main__":
    server()
