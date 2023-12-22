import sys
import logging
import pickle
import time
import socket
import traceback
from queue import Queue
from typing import *

from sync_clip.stuff.sync_signal import *
from sync_clip.utils.util_thread import new_thread

logger = logging.getLogger("sync_clip")


class Client(object):
    MAX_MESSAGE_SIZE = 50 * 1024

    def __init__(self, host="0.0.0.0", port=12364):
        self.host = host
        self.port = port
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_connected = False
        if not self._check_connection():
            sys.exit(1)
        print("confirmed connection !!!")
        self.is_closed = True
        self.recv_sync_sig = Queue()

    def _check_connection(self):
        try:
            self.tcp_socket.connect((self.host, self.port))
            self.is_connected = True
            return True
        except ConnectionRefusedError:
            print(f"\n\n unable to connect to remote server "
                  f"`{self.host}:{self.port}` !!! \n")
            self.is_connected = False
            return False

    def split_sig_data(self, signal: SyncSignal) -> List[SyncSignal]:
        data_length = len(signal.data)
        if data_length <= self.MAX_MESSAGE_SIZE:
            return [signal, ]
        sig_cls = type(signal)
        split_sig_datas = []
        index = 0
        while index < data_length:
            split_data = signal.data[index:index + self.MAX_MESSAGE_SIZE]
            split_sig = sig_cls(data=split_data)
            split_sig.is_end = False
            split_sig_datas.append(split_sig)
            index += self.MAX_MESSAGE_SIZE

        split_sig_datas[-1].is_end = True
        return split_sig_datas

    def send_sync_data(self, signal: SyncSignal):
        sig_datas = self.split_sig_data(signal)
        for sig_data in sig_datas:
            p_sig_data = pickle.dumps(sig_data)
            try:
                data_length = len(p_sig_data)
                header = f"{data_length}".zfill(10)
                p_sig_data = header.encode() + p_sig_data
                # print(f"[client] send length : {data_length}")
                t = self.tcp_socket.send(p_sig_data)
                # print(f"\t\t[client]: sent: {t}")

            except Exception as exp:
                logger.error(f"sending sync data error: {exp} "
                             f"\n{traceback.format_exc()}")

    def _receive_data(self):
        self.tcp_socket.settimeout(0.5)
        header = self.tcp_socket.recv(10)
        if not header:
            raise ConnectionResetError()
        print(f"[client] receive header: {header}, type:{type(header)}")
        data_size = int(header.decode())
        response = self.tcp_socket.recv(data_size)
        print(f"response: {len(response)}, header size: {data_size}")
        if not response:
            raise ConnectionResetError()
        while data_size - len(response) > 0:
            response += self.tcp_socket.recv(data_size - len(response))
        return response

    def merge_recv_sig_data(self) -> SyncSignal:
        rsp = self._receive_data()
        sig: SyncSignal = pickle.loads(rsp)

        while not sig.is_end:
            rsp = self._receive_data()
            next_sig: SyncSignal = pickle.loads(rsp)
            if not isinstance(next_sig, type(sig)):
                logger.error(f"received different type sig !!!")
            sig.data += next_sig.data
            sig.is_end = next_sig.is_end

        return sig

    @new_thread
    def _keep_receiving(self):
        while not self.is_closed:
            # noinspection PyBroadException
            try:
                sig: SyncSignal = self.merge_recv_sig_data()
                if isinstance(sig, SyncData):
                    self.recv_sync_sig.put(sig)

            except socket.timeout:
                continue
            except ConnectionResetError:
                logger.info(f"======== server offline, try to reconnect..."
                            f"==========")
                self.is_connected = False
                while True:
                    self.tcp_socket.close()
                    self.tcp_socket = socket.socket(socket.AF_INET,
                                                    socket.SOCK_STREAM)
                    if self._check_connection():
                        logger.info(
                            f"======== server reconnect success !!!"
                            f"==========")
                        break
                    time.sleep(1)
            except Exception as exp:
                logger.error(f"Exception while receiving: {exp}\n"
                             f"{traceback.format_exc()}")
                continue

    @new_thread
    def _keep_alive(self):
        while not self.is_closed:
            self.send_sync_data(HeartbeatSignal())
            time.sleep(3)

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
            if tc.is_connected:
                tc.send_sync_data(SyncData(f"test: {i}"))
                _sig: SyncData = tc.recv_sync_sig.get(timeout=1)
                print(f"receive from server: {_sig.data}")
                time.sleep(1)
                i += 1
        except Empty:
            continue
