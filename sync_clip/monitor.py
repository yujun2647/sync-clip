import time
import logging
import traceback
from queue import Empty
from threading import Lock

from sync_clip.remote.client import Client
from sync_clip.utils.util_thread import new_thread
from sync_clip.utils.util_hash import hash_data
from sync_clip.stuff.sync_signal import *
from sync_clip.stuff.clipboards import Clipboard

logger = logging.getLogger("sync_clip")


class ClipboardMonitor(object):
    def __init__(self, host="0.0.0.0", port=12364):
        self.this_clip = Clipboard.get_clipboard()
        self.rclip = Client(host=host, port=port)
        self.rclip.start()
        self.is_closed = True
        self._compare_lock = Lock()
        self._last_hash_clip_data = b""

    @new_thread
    def _monitor_remote_clip(self):
        while not self.is_closed:
            # noinspection PyBroadException
            try:
                clip_data: SyncData = self.rclip.recv_sync_sig.get(timeout=5)
                if not clip_data.data.strip():
                    continue
                h_data = hash_data(clip_data.data)
                with self._compare_lock:
                    if h_data != self._last_hash_clip_data:
                        self.this_clip.set_data_to_clip(clip_data.data)
                        self._last_hash_clip_data = h_data
                        sync_sample = clip_data.data[:1000]
                        if isinstance(sync_sample, bytes):
                            sync_sample = sync_sample.decode("utf-8")
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

    @new_thread
    def _monitor_this_clip(self):
        while not self.is_closed:
            # noinspection PyBroadException
            try:
                clip_data: [str, bytes] = self.this_clip.get_data_from_clip()
                if not clip_data.strip():
                    time.sleep(0.3)
                    continue
                h_data = hash_data(clip_data)
                with self._compare_lock:
                    if h_data != self._last_hash_clip_data:
                        self.rclip.send_sync_data(SyncData(clip_data))
                        self._last_hash_clip_data = h_data
                        sync_sample = clip_data[:1000]
                        if isinstance(sync_sample, bytes):
                            sync_sample = sync_sample.decode("utf-8")
                        logger.info(f"""
--------------------------------[sync to remote]--------------------------------
{sync_sample}

--------------------------------[sync to remote]--------------------------------

                        """)
                time.sleep(0.3)
            except Exception as exp:
                logger.error(f"[monitor_this_clip] error: {exp}, \n"
                             f"{traceback.format_exc()}")
                pass

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
