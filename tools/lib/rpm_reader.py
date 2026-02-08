#!/usr/bin/env python3

import io
import threading

from tools.lib.cpio import CpioReader
from tools.lib.in_process_pipe import InProcessPipe
from tools.lib.rpm_file import RpmFileReader
from tools.lib.tree_reader import FileInfo, TreeReader


class RpmReader(TreeReader):
    """Reader for RPM package files."""

    def __init__(self, rpm_path: str):
        self.rpm_path = rpm_path
        self.buf = InProcessPipe()
        self.cpio_reader = CpioReader(stream=self.buf)
        self.done = False
        t = threading.Thread(target=self._unpack_rpm)
        t.start()

    def _unpack_rpm(self):
        """Extract metadata from RPM file."""
        # Open RPM file and parse headers
        with open(self.rpm_path, 'rb') as rpm_file:
            rpm_reader = RpmFileReader(stream=rpm_file, verbose=False)
            rpm_reader.read_headers()
            # Stream CPIO data out
            rpm_reader.stream_cpio(out_stream=self.buf)

    def next(self) -> FileInfo:
        if self.done:
            return None
        info, to_read = self.cpio_reader.read_header_and_content_size()
        if info is None:
            self.done = True
            return None
        # Skip content.
        if to_read > 0:
            file_data = self.cpio_reader.stream.read(to_read)
        return info

    def is_done(self) -> bool:
        return self.done
