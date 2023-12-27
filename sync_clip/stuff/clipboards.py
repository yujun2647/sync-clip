import ctypes
import sys
import time
import shutil
import warnings
import logging
import subprocess
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Union

from pip._internal.cli.main import main

from sync_clip.utils.utiil_image import reduce_image_size

logger = logging.getLogger("sync_clip")


def do_requires_install(require_name):
    main(args=["install", require_name,
               "--index-url", "https://mirrors.aliyun.com/pypi/simple/",
               "--trusted-host", "mirrors.aliyun.com"])


if sys.platform == "win32":
    try:
        import win32clipboard
    except ImportError:
        do_requires_install("pywin32")
        import win32clipboard
    try:
        from PIL import ImageGrab, Image
        from PIL.BmpImagePlugin import DibImageFile
    except ImportError:
        do_requires_install("pillow")
        from PIL import ImageGrab, Image
        from PIL.BmpImagePlugin import DibImageFile

elif sys.platform == "darwin":
    pass


class ClipboardException(Exception):
    ...


class ClipboardSetupException(Exception):
    ...


_TIMEOUT = 0.05


class XclipClipboard(object):

    def __init__(self):
        self.xclip = shutil.which('xclip')
        if not self.xclip:
            raise ClipboardSetupException(
                "xclip must be installed. " "Please install xclip using your system package manager"
            )

    def copy(self, data: Union[str, bytes], encoding: str = None) -> None:
        """
        Copy data into the clipboard

        :param data: the data to be copied to the clipboard. Can be str or bytes.
        :param encoding: same meaning as in ``subprocess.Popen``.
        :return: None
        """
        args = [
            self.xclip,
            '-selection',
            'clipboard',
        ]
        if isinstance(data, bytes):
            if encoding is not None:
                warnings.warn(
                    "encoding specified with a bytes argument. "
                    "Encoding option will be ignored. "
                    "To remove this warning, omit the encoding parameter or specify it as None",
                    stacklevel=2,
                )
            if data.startswith(b"\x89PNG"):
                args.append("-target")
                args.append("image/png")
            proc = subprocess.Popen(
                args,
                stdin=subprocess.PIPE,
                encoding=encoding,
            )
        elif isinstance(data, str):
            proc = subprocess.Popen(
                args,
                stdin=subprocess.PIPE,
                text=True,
                encoding=encoding,
            )
        else:
            raise TypeError(
                f"data argument must be of type str or bytes, not {type(data)}")
        stdout, stderr = proc.communicate(data, timeout=3)
        if proc.returncode != 0:
            raise ClipboardException(
                f"Copy failed. xclip returned code: {proc.returncode!r} "
                f"Stderr: {stderr!r} "
                f"Stdout: {stdout!r}"
            )

    def paste(self, encoding: str = None, text: bool = None,
              errors: str = None):
        """
        Retrieve data from the clipboard

        :param encoding: same meaning as in ``subprocess.run``
        :param text: same meaning as in ``subprocess.run``
        :param errors: same meaning as in ``subprocess.run``
        :return: the clipboard contents. return type is binary by default.
            If any of ``encoding``, ``errors``, or ``text`` are specified, the result type is str
        """
        args = [self.xclip, '-o', '-selection', 'clipboard']
        if encoding or text or errors:
            completed_proc = subprocess.run(
                args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=text,
                encoding=encoding,
                timeout=3
            )
        else:
            # retrieve the available targets and selects the first mime type available or plain text.
            available_targets = [
                t for t in subprocess.check_output(args + ['-t', 'TARGETS'],
                                                   text=True,
                                                   timeout=3).splitlines() if
                t.islower()
            ]
            if "text/plain" in available_targets:
                target = ["-t", "text/plain"]
            elif available_targets:
                target = ["-t", available_targets[0]]
            else:
                target = []

            completed_proc = subprocess.run(
                args + target, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=3
            )

        if completed_proc.returncode != 0:
            raise ClipboardException(
                f"Copy failed. xclip returned code: {completed_proc.returncode!r} "
                f"Stderr: {completed_proc.stderr!r} "
                f"Stdout: {completed_proc.stdout!r}"
            )
        return completed_proc.stdout

    def clear(self):
        """
        Clear the clipboard contents

        :return:
        """
        self.copy('')


class Clipboard(ABC):

    @abstractmethod
    def read_clip(self):
        pass

    @abstractmethod
    def write_clip(self, byte_data):
        pass

    @classmethod
    def get_clipboard(cls):
        if sys.platform == "win32":
            return WindowsClipboard()
        elif sys.platform == "darwin":
            pass
        elif sys.platform == "linux":
            return LinuxClipboard()


class WindowsClipboard(Clipboard):

    def __init__(self):
        super().__init__()
        self._is_open = False
        self._clip = win32clipboard

    def write_clip(self, data):
        if not data.strip():
            return
        print(f"byte_data: {data[:10]}, \n"
              f"length: {len(data)},\n"
              f"type: {type(data)}")
        try:
            if isinstance(data, bytes) and data.startswith(b"\x89PNG"):
                # image
                input_data = BytesIO(data)
                image = Image.open(input_data)
                output = BytesIO()
                image.convert("RGB").save(output, "BMP")
                data = output.getvalue()[14:]
                output.close()
                with self:
                    win32clipboard.EmptyClipboard()
                    self._clip.SetClipboardData(win32clipboard.CF_DIB, data)
            else:
                with self:
                    self._clip.EmptyClipboard()
                    if isinstance(data, str):
                        self._clip.SetClipboardText(data, 13)
                    elif isinstance(data, bytes):
                        data = data.decode("utf-8")
                        self._clip.SetClipboardText(data, 13)

        finally:
            pass

    def read_clip(self):
        # noinspection PyBroadException
        try:
            with self:
                data = self._clip.GetClipboardData()
                return data
        except TypeError:
            # noinspection PyBroadException
            try:
                buffer = BytesIO()
                im: DibImageFile = ImageGrab.grabclipboard()
                im.save(buffer, 'PNG')
                data = buffer.getvalue()
                return data
            except Exception as exp:
                logger.error(f"read clipboard failed, error: {exp}")
                return ""

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self, *, _timeout=None):
        import pywintypes
        if self._is_open:
            return self
        try:
            self._clip.OpenClipboard()
            self._is_open = True
        except pywintypes.error as e:
            if e.winerror == 5:
                if _timeout:
                    if time.time() < _timeout:
                        time.sleep(0.001)
                        return self.open(_timeout=_timeout)
                    else:
                        raise
                else:
                    t = time.time() + _TIMEOUT
                    time.sleep(0.001)
                    return self.open(_timeout=t)
        return self

    def close(self):
        import pywintypes
        try:
            self._clip.CloseClipboard()
            self._is_open = False
        except pywintypes.error as e:
            if e.winerror == 1418:
                self._is_open = False
                return
            raise


class LinuxClipboard(Clipboard):

    def __init__(self):
        self._clip = XclipClipboard()
        super().__init__()

    def read_clip(self):
        # noinspection PyBroadException
        try:
            text = self._clip.paste()
        except Exception as exp:
            logger.error(f"read clipboard failed, error: {exp}")

            return ""
        return text

    def write_clip(self, byte_data):
        byte_data, _ = reduce_image_size(byte_data)
        self._clip.copy(byte_data)
