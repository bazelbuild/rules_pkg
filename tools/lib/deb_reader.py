import io
import lzma
import threading

from tools.lib.in_process_pipe import InProcessPipe
from tools.lib.tar_reader import TarReader
from tools.lib.tree_reader import FileInfo, TreeReader

BLOCKSIZE = 65536


class ArReader:
    """Reader for ar archive format (used in .deb packages)."""

    AR_MAGIC = b"!<arch>\n"

    def __init__(self, ar_path: str):
        """Initialize ArReader with path to ar archive."""
        self.ar_path = ar_path
        self.data_tar = None
        self.data_tar_name = None
        self._read_ar_archive()

    def _read_ar_archive(self):
        """Read ar archive and extract data.tar.xz."""
        try:
            with open(self.ar_path, 'rb') as f:
                # Check magic bytes
                magic = f.read(8)
                if magic != self.AR_MAGIC:
                    raise ValueError(f"Not a valid ar archive: expected magic {self.AR_MAGIC}, got {magic}")

                # Read entries until we find data.tar.*
                while True:
                    entry_name, entry_size = self._read_ar_entry_header(f)
                    if entry_name is None:
                        break

                    if entry_name.startswith("data.tar"):
                        # Found it! Read the data
                        self.data_tar_name = entry_name
                        self.data_tar = f.read(entry_size)
                        return
                    else:
                        # Skip this entry
                        # Entries are padded to even boundaries
                        padded_size = entry_size if entry_size % 2 == 0 else entry_size + 1
                        f.seek(padded_size, 1)  # Relative seek

                if self.data_tar is None:
                    raise ValueError("data.tar.* not found in ar archive")

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Error reading ar archive {self.ar_path}: {e}")

    def _read_ar_entry_header(self, f):
        """Read ar entry header and return (filename, size).

        AR entry header format (60 bytes):
        - Bytes 0-15: File name (null-padded)
        - Bytes 16-27: Modification time (decimal string)
        - Bytes 28-33: Owner ID (decimal string)
        - Bytes 34-39: Group ID (decimal string)
        - Bytes 40-45: File mode (octal string)
        - Bytes 46-57: File size (decimal string)
        - Bytes 58-59: File magic ("`\\n")
        """
        header = f.read(60)
        if len(header) < 60:
            return None, None

        # Validate magic bytes at end
        if header[58:60] != b"`\n":
            return None, None

        # Extract filename (remove trailing spaces/nulls/slash)
        filename = header[0:16].rstrip(b' \0/').decode('ascii')

        # Extract file size (decimal string)
        try:
            size_str = header[46:58].rstrip(b' ').decode('ascii')
            size = int(size_str)
        except (ValueError, UnicodeDecodeError):
            raise ValueError(f"Invalid ar entry header: can't parse size from {header[46:58]}")

        return filename, size

    def get_tar_stream(self):
        """Return decompressed tar stream from data.tar.*."""
        if self.data_tar is None:
            raise ValueError("data.tar.* not found in archive")

        name = self.data_tar_name
        try:
            if name.endswith('.xz') or name.endswith('.lzma'):
                decompressed = lzma.decompress(self.data_tar)
            elif name.endswith('.gz'):
                import gzip
                decompressed = gzip.decompress(self.data_tar)
            elif name.endswith('.bz2'):
                import bz2
                decompressed = bz2.decompress(self.data_tar)
            else:
                decompressed = self.data_tar
            return io.BytesIO(decompressed)
        except Exception as e:
            raise ValueError(f"Error decompressing {name}: {e}")


class DebReader(TreeReader):
    """Reader for .deb packages (ar archives containing data.tar.*)."""

    def __init__(self, deb_path: str):
        """Initialize DebReader with path to .deb file.

        Args:
            deb_path: Path to .deb package file
        """
        self.deb_path = deb_path
        self.buf = InProcessPipe()
        self.done = False
        t = threading.Thread(target=self._unpack_deb)
        t.start()
        self.tar_reader = TarReader(tar_stream=self.buf)

    def _unpack_deb(self):
        """Read ar archive, decompress tar stream, and write to pipe."""
        try:
            ar_reader = ArReader(self.deb_path)
            tar_stream = ar_reader.get_tar_stream()
            while True:
                block = tar_stream.read(BLOCKSIZE)
                if not block:
                    break
                self.buf.write(block)
        finally:
            self.buf.close()

    def next(self) -> FileInfo:
        """Return the next FileInfo, or None if no more items."""
        if self.done:
            return None
        info = self.tar_reader.next()
        if info is None:
            self.done = True
        return info

    def is_done(self) -> bool:
        """Return True if all items have been read."""
        return self.done
