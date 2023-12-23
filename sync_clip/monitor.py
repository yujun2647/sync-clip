import time
import logging
import traceback
from queue import Empty
from threading import Lock

from sync_clip.remote.client import Client
from sync_clip.utils.util_thread import new_thread
from sync_clip.utils.util_hash import hash_data
from sync_clip.utils.utiil_image import reduce_image_size
from sync_clip.stuff.sync_signal import *
from sync_clip.stuff.clipboards import Clipboard

logger = logging.getLogger("sync_clip")


class ClipboardMonitor(object):
    def __init__(self, host="0.0.0.0", port=12364):
        self.tclip = Clipboard.get_clipboard()
        self.rclip = Client(host=host, port=port)
        self.rclip.start()
        self.is_closed = True
        self._compare_lock = Lock()
        self._last_hash_clip_data = b""
        self._last_get_remote_time = time.time()

    @classmethod
    def data_is_png_image(cls, data):
        return isinstance(data, bytes) and data.startswith(b"\x89PNG")

    @new_thread
    def _monitor_this_clip(self):
        while not self.is_closed:
            # noinspection PyBroadException
            try:
                time.sleep(0.3)
                with self._compare_lock:
                    clip_data: [str, bytes] = self.tclip.read_clip()
                    if not clip_data.strip():
                        continue

                    if self.data_is_png_image(clip_data):
                        # prevent large image
                        a = time.time()
                        clip_data, reduced = reduce_image_size(clip_data)
                        if reduced:
                            print(
                                f"Reduced image cost: {round(time.time() - a, 2)}")
                            self.tclip.write_clip(clip_data)

                    h_data = hash_data(clip_data)
                    if h_data != self._last_hash_clip_data:
                        self._last_hash_clip_data = h_data
                        if time.time() - self._last_get_remote_time < 0.5:
                            # same image different bytes datas
                            continue
                        self.rclip.send_sync_data(SyncData(clip_data))
                        sync_sample = clip_data[:500]
                        if isinstance(sync_sample, bytes):
                            try:
                                sync_sample = sync_sample.decode("utf-8")
                            except UnicodeDecodeError:
                                pass
                        logger.info(f"""
--------------------------------[sync to remote]--------------------------------
{sync_sample}
--------------------------------[sync to remote]--------------------------------

                                    """)
            except Exception as exp:
                logger.error(f"[monitor_this_clip] error: {exp}, \n"
                             f"{traceback.format_exc()}")
                pass

    @new_thread
    def _monitor_remote_clip(self):
        while not self.is_closed:
            # noinspection PyBroadException
            try:
                clip_data: SyncData = self.rclip.recv_sync_sig.get(timeout=5)
                if not clip_data.data.strip():
                    continue
                if not isinstance(clip_data.data, bytes):
                    clip_data.data = clip_data.data.encode()
                    print("data is not bytes, force to convert")

                # union format, windows clipboard will add '\r' before '\n'
                if not clip_data.data.startswith(b"\x89PNG"):
                    clip_data.data = clip_data.data.replace(b"\r\n", b"\n")

                compare_data = clip_data.data
                if not isinstance(compare_data, bytes):
                    compare_data = compare_data.encode()

                h_data = hash_data(compare_data)
                with self._compare_lock:
                    if h_data != self._last_hash_clip_data:
                        self.tclip.write_clip(clip_data.data)
                        self._last_hash_clip_data = h_data
                        self._last_get_remote_time = time.time()
                        sync_sample = clip_data.data[:500]
                        if isinstance(sync_sample, bytes):
                            try:
                                sync_sample = sync_sample.decode("utf-8")
                            except UnicodeDecodeError:
                                pass
                        logger.info(f"""
-------------------------------[sync from remote]-------------------------------
{sync_sample}
-------------------------------[sync from remote]-------------------------------

                        """)
            except Empty:
                pass
            except Exception as exp:
                logger.error(f"[monitor_remote_clip] error: {exp}, \n"
                             f"{traceback.format_exc()}")

    def start(self):
        # noinspection PyBroadException
        try:
            self.is_closed = False
            self._monitor_this_clip()
            self._monitor_remote_clip()
        except Exception as exp:
            logger.error(f"Monitor start failed: {exp}, \n"
                         f"{traceback.format_exc()}")
            self.close()
            return False

    def close(self):
        if hasattr(self, "rclip"):
            self.rclip.close()
        if hasattr(self, "is_closed"):
            self.is_closed = True

    def __del__(self):
        self.close()


def monitor(host="0.0.0.0", port=12364):
    from sync_clip.utils.util_log import set_scripts_logging

    set_scripts_logging(__file__, logger=logger, level=logging.DEBUG,
                        console_log=True, file_mode="a")
    ClipboardMonitor(host=host, port=port).start()


if __name__ == "__main__":
    monitor()
