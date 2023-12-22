import sys
import time
import pickle
import socket
import logging
import traceback
from queue import Queue
from socket import SOL_SOCKET, SO_REUSEADDR

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
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # prevent system keep address
        self.tcp_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.tcp_socket.bind((self.host, self.port))
        self.tcp_socket.listen(10)
        self.client_heartbeat_q = Queue()
        self.sending_msg_queue = Queue()
        self.is_closed = True
        self.client_set = {}
        self.conns = []

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
        logger.info(f"receiving data from {this_addr}: {sig.data[:20]}")
        for conn, addr in self.conns:
            if addr != this_addr:
                self._send_sync_data(conn, addr, sig)

    def _send_sync_data(self, conn: socket.socket, addr, sig: SyncSignal):
        p_sig_data = pickle.dumps(sig)
        try:
            data_length = len(p_sig_data)
            header = f"{data_length}".zfill(10)
            p_sig_data = header.encode() + p_sig_data
            conn.send(p_sig_data)
        except BrokenPipeError:
            self.conns.remove((conn, addr))
            conn.close()
        except Exception as exp:
            logger.error(f"sending sync data error: {exp} "
                         f"\n{traceback.format_exc()}")

    @classmethod
    def _receive_data(cls, conn: socket.socket):
        conn.settimeout(0.5)
        header = conn.recv(10)
        if not header:
            raise ConnectionResetError()
        data_size = int(header.decode())
        response = conn.recv(data_size)
        if not response:
            raise ConnectionResetError()
        while data_size - len(response) > 0:
            response += conn.recv(data_size - len(response))
        return response

    @new_thread
    def _keep_receiving(self, conn: socket.socket, addr: tuple):
        while not self.is_closed:
            try:
                response = self._receive_data(conn)
                sig: SyncSignal = pickle.loads(response)
                assert isinstance(sig, SyncSignal)
                if isinstance(sig, SyncData):
                    self._broadcast_sync_data(sig, addr)
                elif isinstance(sig, HeartbeatSignal):
                    pass
            except socket.timeout:
                continue
            except ConnectionResetError:
                self.conns.remove((conn, addr))
                conn.close()
                logger.info(f"client exit: {addr}")
                break
            except Exception as exp:
                logger.error(f"exception: {exp}, \n"
                             f"{traceback.format_exc()}")
                # print(f"debug: {exp}, {response}")
                break
        logger.info(f"client: {addr} listening thread end")

    def _keep_accept_conn(self):
        try:
            while not self.is_closed:
                # noinspection PyBroadException
                try:
                    self.tcp_socket.settimeout(0.5)
                    conn, addr = self.tcp_socket.accept()
                    self.conns.append((conn, addr))
                    self._keep_receiving(conn, addr)
                    logger.info(f"new connection from {addr}")
                except socket.timeout:
                    continue
                except Exception as exp:
                    logger.error(f"Exception while receiving: {exp}\n"
                                 f"{traceback.format_exc()}")
                    continue
        except KeyboardInterrupt:
            self.close()
            return

    def start(self):
        self.is_closed = False
        logger.info(f"\n\n\t[Server starting] listening on "
                    f"`{self.host}:{self.port}`")
        self._keep_accept_conn()

    def close(self):
        self.tcp_socket.close()
        if hasattr(self, "conns"):
            for conn, addr in self.conns:
                conn.close()
            self.conns.clear()
        self.is_closed = True

    def __del__(self):
        self.close()


def server(port=12365):
    from sync_clip.utils.util_log import set_scripts_logging

    set_scripts_logging(__file__, logger=logger, level=logging.DEBUG,
                        console_log=True, file_mode="a")
    Server(port=port).start()


if __name__ == "__main__":
    server()
